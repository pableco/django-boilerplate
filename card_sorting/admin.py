from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse

from .importer import import_cards
from .models import Card, CardPlacement, Category, SortingSession

LEVEL_CHOICES = [
    ('Level 0', 'Level 0'),
    ('Level 1', 'Level 1'),
    ('Level 2', 'Level 2'),
    ('Level 3', 'Level 3'),
    ('Level 4', 'Level 4'),
    ('', 'Sin nivel'),
]


class CsvImportForm(forms.Form):
    csv_file = forms.FileField(label='Fichero CSV')
    levels = forms.MultipleChoiceField(
        label='Niveles a importar',
        choices=LEVEL_CHOICES,
        initial=['Level 0', 'Level 1'],
        widget=forms.CheckboxSelectMultiple,
    )
    replace = forms.BooleanField(
        label='Sustituir el set actual',
        required=False,
        help_text='Las tarjetas que no estén en el CSV se retiran de la prueba. '
                  'No se borran, así que sus resultados anteriores se conservan.',
    )
    skip_deprecated = forms.BooleanField(
        label='Omitir filas marcadas como DEPRECATED', required=False, initial=True,
    )


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    change_list_template = 'admin/card_sorting/card/change_list.html'
    list_display = ['title', 'level', 'main_menu', 'traffic', 'is_active']
    list_editable = ['is_active']
    list_filter = ['is_active', 'level', 'main_menu']
    search_fields = ['title', 'main_menu', 'path']
    ordering = ['order', 'title']
    list_per_page = 200
    actions = ['activate', 'deactivate']
    fieldsets = [
        (None, {'fields': ['title', 'description', 'is_active', 'order']}),
        ('Datos del CSV', {
            'classes': ['collapse'],
            'fields': ['level', 'main_menu', 'parent_page', 'path', 'url', 'status', 'traffic'],
        }),
    ]

    @admin.action(description='Incluir en la prueba')
    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} tarjetas incluidas en la prueba.')

    @admin.action(description='Retirar de la prueba (conserva resultados)')
    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} tarjetas retiradas de la prueba.')

    def get_urls(self):
        return [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='card_sorting_card_import'),
        ] + super().get_urls()

    def import_csv(self, request):
        form = CsvImportForm(request.POST or None, request.FILES or None)
        if request.method == 'POST' and form.is_valid():
            raw = form.cleaned_data['csv_file'].read()
            try:
                text = raw.decode('utf-8-sig')
            except UnicodeDecodeError:
                text = raw.decode('latin-1')  # Excel on Windows
            try:
                result = import_cards(
                    text,
                    levels=form.cleaned_data['levels'],
                    replace=form.cleaned_data['replace'],
                    skip_deprecated=form.cleaned_data['skip_deprecated'],
                )
            except ValueError as exc:
                form.add_error('csv_file', str(exc))
            else:
                self.message_user(request, f'Importación completada: {result}.', messages.SUCCESS)
                return redirect(reverse('admin:card_sorting_card_changelist'))
        return render(request, 'admin/card_sorting/card/import_csv.html', {
            **self.admin_site.each_context(request),
            'title': 'Importar tarjetas desde CSV',
            'opts': self.model._meta,
            'form': form,
        })


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


admin.site.site_header = 'Card Sorting'
admin.site.site_title = 'Card Sorting'
admin.site.index_title = 'Gestión de la prueba'
