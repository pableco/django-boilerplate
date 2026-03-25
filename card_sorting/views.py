import json
from collections import defaultdict

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Card, CardPlacement, Category, SortingSession


def index(request):
    return redirect('card_sorting:start')


def start_session(request):
    if request.method == 'POST':
        name = request.POST.get('participant_name', '').strip()
        email = request.POST.get('participant_email', '').strip()
        role = request.POST.get('participant_role', '').strip()

        if not name:
            return render(request, 'card_sorting/start.html', {
                'error': 'El nombre es obligatorio.'
            })

        session = SortingSession.objects.create(
            participant_name=name,
            participant_email=email,
            participant_role=role,
        )

        # Pre-create a CardPlacement for every active card
        cards = Card.objects.filter(is_active=True)
        CardPlacement.objects.bulk_create([
            CardPlacement(session=session, card=card, position=i)
            for i, card in enumerate(cards)
        ])

        return redirect('card_sorting:sort', session_key=session.session_key)

    return render(request, 'card_sorting/start.html')


def sort_cards(request, session_key):
    session = get_object_or_404(SortingSession, session_key=session_key)

    if session.is_complete:
        return redirect('card_sorting:done', session_key=session_key)

    placements = (
        session.cardplacement_set
        .select_related('card', 'category')
        .order_by('position')
    )
    categories = session.categories.all()

    unsorted = [p for p in placements if p.category is None]
    sorted_by_cat = defaultdict(list)
    for p in placements:
        if p.category:
            sorted_by_cat[p.category_id].append(p)

    return render(request, 'card_sorting/sort.html', {
        'session': session,
        'unsorted': unsorted,
        'categories': categories,
        'sorted_by_cat': dict(sorted_by_cat),
    })


@require_POST
def save_sort(request, session_key):
    """AJAX endpoint: receives the full current state and persists it."""
    session = get_object_or_404(SortingSession, session_key=session_key)

    if session.is_complete:
        return JsonResponse({'ok': False, 'error': 'Session already complete'}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    # data format:
    # {
    #   "categories": [{"id": null|int, "name": "...", "cards": [card_id, ...]}],
    #   "unsorted": [card_id, ...]
    # }
    categories_data = data.get('categories', [])
    unsorted_ids = data.get('unsorted', [])

    # Build/update categories
    existing_ids = set(session.categories.values_list('id', flat=True))
    sent_ids = set()

    for pos, cat_data in enumerate(categories_data):
        cat_id = cat_data.get('id')
        name = cat_data.get('name', 'Sin nombre').strip() or 'Sin nombre'
        card_ids = cat_data.get('cards', [])

        if cat_id and cat_id in existing_ids:
            cat = Category.objects.get(id=cat_id, session=session)
            cat.name = name
            cat.position = pos
            cat.save()
            sent_ids.add(cat_id)
        else:
            cat = Category.objects.create(session=session, name=name, position=pos)
            sent_ids.add(cat.id)

        # Update placements for cards in this category
        for card_pos, card_id in enumerate(card_ids):
            CardPlacement.objects.filter(session=session, card_id=card_id).update(
                category=cat, position=card_pos
            )

    # Delete categories that were removed
    Category.objects.filter(session=session, id__in=existing_ids - sent_ids).delete()

    # Clear category for unsorted cards
    CardPlacement.objects.filter(session=session, card_id__in=unsorted_ids).update(
        category=None
    )

    return JsonResponse({'ok': True})


@require_POST
def complete_session(request, session_key):
    session = get_object_or_404(SortingSession, session_key=session_key)

    if not session.is_complete:
        # Save final state first
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = {}

        if data:
            # Re-use save logic
            _persist_sort_data(session, data)

        session.complete()

    return JsonResponse({'ok': True, 'redirect': f'/done/{session_key}/'})


def _persist_sort_data(session, data):
    categories_data = data.get('categories', [])
    unsorted_ids = data.get('unsorted', [])
    existing_ids = set(session.categories.values_list('id', flat=True))
    sent_ids = set()

    for pos, cat_data in enumerate(categories_data):
        cat_id = cat_data.get('id')
        name = cat_data.get('name', 'Sin nombre').strip() or 'Sin nombre'
        card_ids = cat_data.get('cards', [])

        if cat_id and cat_id in existing_ids:
            cat = Category.objects.get(id=cat_id, session=session)
            cat.name = name
            cat.position = pos
            cat.save()
            sent_ids.add(cat_id)
        else:
            cat = Category.objects.create(session=session, name=name, position=pos)
            sent_ids.add(cat.id)

        for card_pos, card_id in enumerate(card_ids):
            CardPlacement.objects.filter(session=session, card_id=card_id).update(
                category=cat, position=card_pos
            )

    Category.objects.filter(session=session, id__in=existing_ids - sent_ids).delete()
    CardPlacement.objects.filter(session=session, card_id__in=unsorted_ids).update(category=None)


def session_done(request, session_key):
    session = get_object_or_404(SortingSession, session_key=session_key)
    return render(request, 'card_sorting/done.html', {'session': session})


@staff_member_required
def results(request):
    sessions = SortingSession.objects.filter(is_complete=True).prefetch_related(
        'categories', 'cardplacement_set__card', 'cardplacement_set__category'
    )
    cards = Card.objects.filter(is_active=True)

    # For each card, count how many times it appeared in each category name
    card_stats = {}
    for card in cards:
        category_counts = defaultdict(int)
        placements = CardPlacement.objects.filter(
            card=card, session__is_complete=True, category__isnull=False
        ).select_related('category')
        for p in placements:
            category_counts[p.category.name] += 1
        card_stats[card.id] = {
            'card': card,
            'category_counts': dict(sorted(category_counts.items(), key=lambda x: -x[1])),
            'total_sorted': sum(category_counts.values()),
        }

    # Co-occurrence matrix: how often two cards are in the same category
    completed_sessions = list(sessions)
    all_card_ids = list(cards.values_list('id', flat=True))
    cooccurrence = defaultdict(lambda: defaultdict(int))

    for session in completed_sessions:
        placements = list(session.cardplacement_set.filter(category__isnull=False))
        by_category = defaultdict(list)
        for p in placements:
            by_category[p.category_id].append(p.card_id)
        for cat_cards in by_category.values():
            for i, c1 in enumerate(cat_cards):
                for c2 in cat_cards[i + 1:]:
                    cooccurrence[c1][c2] += 1
                    cooccurrence[c2][c1] += 1

    return render(request, 'card_sorting/results.html', {
        'sessions': sessions,
        'session_count': len(completed_sessions),
        'cards': cards,
        'card_stats': card_stats,
    })
