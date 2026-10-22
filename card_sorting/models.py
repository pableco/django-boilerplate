import uuid
from django.db import models
from django.utils import timezone


class Card(models.Model):
    title = models.CharField('nombre', max_length=200)
    description = models.TextField('descripción', blank=True)
    order = models.IntegerField('orden', default=0)
    is_active = models.BooleanField(
        'en la prueba', default=True,
        help_text='Solo las tarjetas activas se muestran a los participantes.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Metadata from the information-architecture CSV. Never shown to
    # participants (it would bias the sort); used to filter and analyse.
    level = models.CharField('nivel', max_length=20, blank=True)
    main_menu = models.CharField('menú actual', max_length=100, blank=True)
    parent_page = models.CharField('página padre', max_length=300, blank=True)
    path = models.CharField(max_length=500, blank=True)
    url = models.URLField(max_length=500, blank=True)
    status = models.CharField('estado', max_length=100, blank=True)
    traffic = models.PositiveIntegerField('tráfico 90 días', default=0)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class SortingSession(models.Model):
    session_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    participant_name = models.CharField(max_length=200)
    participant_email = models.EmailField(blank=True)
    participant_role = models.CharField(max_length=200, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.participant_name} — {self.started_at.strftime('%Y-%m-%d %H:%M')}"

    def complete(self):
        self.is_complete = True
        self.completed_at = timezone.now()
        self.save()

    @property
    def duration_minutes(self):
        if self.completed_at and self.started_at:
            delta = self.completed_at - self.started_at
            return round(delta.total_seconds() / 60, 1)
        return None

    @property
    def cards_sorted(self):
        return self.cardplacement_set.filter(category__isnull=False).count()

    @property
    def total_cards(self):
        return self.cardplacement_set.count()


class Category(models.Model):
    session = models.ForeignKey(SortingSession, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=200)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'created_at']

    def __str__(self):
        return f"{self.session.participant_name} → {self.name}"


class CardPlacement(models.Model):
    session = models.ForeignKey(SortingSession, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.IntegerField(default=0)

    class Meta:
        unique_together = [('session', 'card')]

    def __str__(self):
        cat = self.category.name if self.category else 'Sin categoría'
        return f"{self.card.title} → {cat}"
