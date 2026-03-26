from django.contrib import admin
from .models import Card, SortingSession, Category, CardPlacement


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'description']
    ordering = ['order']


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0
    readonly_fields = ['created_at']


class CardPlacementInline(admin.TabularInline):
    model = CardPlacement
    extra = 0
    readonly_fields = ['card', 'category', 'position']
    can_delete = False


@admin.register(SortingSession)
class SortingSessionAdmin(admin.ModelAdmin):
    list_display = ['participant_name', 'participant_email', 'participant_role',
                    'is_complete', 'started_at', 'completed_at']
    list_filter = ['is_complete']
    search_fields = ['participant_name', 'participant_email']
    readonly_fields = ['session_key', 'started_at', 'completed_at']
    inlines = [CategoryInline, CardPlacementInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'session', 'position']
    list_filter = ['session']


@admin.register(CardPlacement)
class CardPlacementAdmin(admin.ModelAdmin):
    list_display = ['card', 'session', 'category']
    list_filter = ['category', 'session']
