import json
from collections import Counter, defaultdict
from itertools import combinations

from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Card, CardPlacement, Category, SortingSession


def index(request):
    return redirect('card_sorting:start')


def start_session(request):
    card_count = Card.objects.filter(is_active=True).count()
    if request.method == 'POST':
        name = request.POST.get('participant_name', '').strip()
        if not name:
            return render(request, 'card_sorting/start.html', {
                'error': 'El nombre es obligatorio.', 'card_count': card_count,
            })

        session = SortingSession.objects.create(
            participant_name=name,
            participant_email=request.POST.get('participant_email', '').strip(),
            participant_role=request.POST.get('participant_role', '').strip(),
        )
        # Shuffle per participant so card order does not bias the groupings.
        cards = Card.objects.filter(is_active=True).order_by('?')
        CardPlacement.objects.bulk_create([
            CardPlacement(session=session, card=card, position=i)
            for i, card in enumerate(cards)
        ])
        return redirect('card_sorting:sort', session_key=session.session_key)

    return render(request, 'card_sorting/start.html', {'card_count': card_count})


def sort_cards(request, session_key):
    session = get_object_or_404(SortingSession, session_key=session_key)
    if session.is_complete:
        return redirect('card_sorting:done', session_key=session_key)

    placements = session.cardplacement_set.select_related('card').order_by('position')
    by_category = defaultdict(list)
    unsorted = []
    for p in placements:
        (by_category[p.category_id] if p.category_id else unsorted).append(p)

    categories = list(session.categories.all())
    for cat in categories:
        cat.placements = by_category.get(cat.id, [])

    return render(request, 'card_sorting/sort.html', {
        'session': session,
        'unsorted': unsorted,
        'categories': categories,
    })


@transaction.atomic
def _persist_sort_data(session, data):
    """Store the full board state sent by the browser.

    data = {"categories": [{"id": int|null, "name": str, "cards": [card_id]}],
            "unsorted": [card_id]}
    Returns the category ids in the order received, so the browser can keep
    them and stop creating a new category on every autosave.
    """
    existing = {c.id: c for c in session.categories.all()}
    kept_ids = []

    for pos, cat_data in enumerate(data.get('categories', [])):
        name = (cat_data.get('name') or '').strip()[:200] or 'Sin nombre'
        cat = existing.get(cat_data.get('id'))
        if cat:
            if (cat.name, cat.position) != (name, pos):
                cat.name, cat.position = name, pos
                cat.save(update_fields=['name', 'position'])
        else:
            cat = Category.objects.create(session=session, name=name, position=pos)
        kept_ids.append(cat.id)

        for card_pos, card_id in enumerate(cat_data.get('cards', [])):
            CardPlacement.objects.filter(session=session, card_id=card_id).update(
                category=cat, position=card_pos
            )

    Category.objects.filter(session=session).exclude(id__in=kept_ids).delete()
    CardPlacement.objects.filter(session=session, card_id__in=data.get('unsorted', [])).update(category=None)
    return kept_ids


def _load_json(request):
    try:
        data = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


@require_POST
def save_sort(request, session_key):
    session = get_object_or_404(SortingSession, session_key=session_key)
    if session.is_complete:
        return JsonResponse({'ok': False, 'error': 'Session already complete'}, status=400)
    data = _load_json(request)
    if data is None:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'ok': True, 'category_ids': _persist_sort_data(session, data)})


@require_POST
def complete_session(request, session_key):
    session = get_object_or_404(SortingSession, session_key=session_key)
    if not session.is_complete:
        data = _load_json(request)
        if data:
            _persist_sort_data(session, data)
        session.complete()
    return JsonResponse({'ok': True})


def session_done(request, session_key):
    session = get_object_or_404(SortingSession, session_key=session_key)
    return render(request, 'card_sorting/done.html', {'session': session})


@staff_member_required
def results(request):
    sessions = list(SortingSession.objects.filter(is_complete=True))
    session_count = len(sessions)
    cards = {c.id: c for c in Card.objects.filter(is_active=True)}

    placements = (
        CardPlacement.objects
        .filter(session__is_complete=True, category__isnull=False, card_id__in=cards)
        .values_list('card_id', 'category_id', 'category__name')
    )

    # Participants type category names freely: count "Gestión" and "gestión "
    # as the same group, and display the spelling used most often.
    label_counts = defaultdict(Counter)
    per_card = defaultdict(Counter)
    members = defaultdict(list)
    for card_id, category_id, name in placements:
        key = name.strip().casefold()
        label_counts[key][name.strip()] += 1
        per_card[card_id][key] += 1
        members[category_id].append(card_id)

    def label(key):
        return label_counts[key].most_common(1)[0][0]

    card_stats = []
    for card_id, card in cards.items():
        counts = per_card.get(card_id, Counter())
        total = sum(counts.values())
        top = counts.most_common()
        card_stats.append({
            'card': card,
            'total_sorted': total,
            'groups': [(label(k), n) for k, n in top],
            # Share of participants who agree on the most common group.
            'agreement': round(100 * top[0][1] / total) if total else 0,
        })
    card_stats.sort(key=lambda s: (-s['agreement'], s['card'].title))

    pair_counts = Counter()
    for card_ids in members.values():
        for a, b in combinations(sorted(set(card_ids)), 2):
            pair_counts[(a, b)] += 1
    top_pairs = [
        {
            'a': cards[a], 'b': cards[b], 'count': n,
            'pct': round(100 * n / session_count) if session_count else 0,
        }
        for (a, b), n in pair_counts.most_common(30)
    ]

    durations = [s.duration_minutes for s in sessions if s.duration_minutes is not None]
    category_counts = Counter(
        Category.objects.filter(session__is_complete=True).values_list('session_id', flat=True)
    )

    return render(request, 'card_sorting/results.html', {
        'sessions': sessions,
        'session_count': session_count,
        'card_count': len(cards),
        'card_stats': card_stats,
        'top_pairs': top_pairs,
        'avg_duration': round(sum(durations) / len(durations), 1) if durations else None,
        'avg_categories': round(sum(category_counts.values()) / session_count, 1) if session_count else None,
    })
