import uuid
from django.db import models
from django.utils import timezone


class Card(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
