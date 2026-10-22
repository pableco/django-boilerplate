"""Import cards from the information-architecture CSV export.

Expected columns (extra columns are ignored): Name, Page Level, Parent Page,
path, Main menu, url, Status, "Tráfico en 90 días", DEPRECATED.
"""
import csv
import io

from django.db import transaction

from .models import Card

DEFAULT_LEVELS = ('Level 0', 'Level 1')


class ImportResult:
    def __init__(self):
        self.created = 0
        self.updated = 0
        self.deactivated = 0
        self.skipped = 0

    def __str__(self):
        parts = [f'{self.created} creadas', f'{self.updated} actualizadas']
        if self.deactivated:
            parts.append(f'{self.deactivated} retiradas de la prueba')
        if self.skipped:
            parts.append(f'{self.skipped} filas omitidas')
        return ', '.join(parts)


def _traffic(value):
    digits = (value or '').strip().replace('.', '').replace(',', '')
    return int(digits) if digits.isdigit() else 0


def read_rows(text):
    """Parse CSV text (BOM tolerated) into dicts with stripped keys/values."""
    reader = csv.DictReader(io.StringIO(text.lstrip('﻿')))
    if not reader.fieldnames or 'Name' not in [f.strip() for f in reader.fieldnames]:
        raise ValueError('El CSV no tiene la columna "Name". ¿Es el export correcto?')
    for row in reader:
        yield {(k or '').strip(): (v or '').strip() for k, v in row.items()}


@transaction.atomic
def import_cards(text, levels=DEFAULT_LEVELS, replace=False, skip_deprecated=True):
    """Create or update one card per CSV row, matched by name.

    With replace=True, cards absent from the CSV are taken out of the test
    (is_active=False) rather than deleted, so their past results survive.
    """
    result = ImportResult()
    levels = set(levels) if levels else None
    seen_ids = []

    for order, row in enumerate(read_rows(text), start=1):
        name = row.get('Name', '')
        level = row.get('Page Level', '')
        if not name or (levels and level not in levels):
            result.skipped += 1
            continue
        if skip_deprecated and row.get('DEPRECATED'):
            result.skipped += 1
            continue

        card, created = Card.objects.update_or_create(
            title=name,
            defaults={
                'level': level,
                'main_menu': row.get('Main menu', ''),
                'parent_page': row.get('Parent Page', ''),
                'path': row.get('path', ''),
                'url': row.get('url', ''),
                'status': row.get('Status', ''),
                'traffic': _traffic(row.get('Tráfico en 90 días')),
                'order': order,
                'is_active': True,
            },
        )
        seen_ids.append(card.id)
        if created:
            result.created += 1
        else:
            result.updated += 1

    if replace:
        result.deactivated = (
            Card.objects.filter(is_active=True).exclude(id__in=seen_ids).update(is_active=False)
        )
    return result
