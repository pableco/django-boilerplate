from pathlib import Path

from django.core.management.base import BaseCommand

from card_sorting.importer import import_cards
from card_sorting.models import Card

INITIAL_CSV = Path(__file__).resolve().parents[2] / 'data' / 'initial_items.csv'


class Command(BaseCommand):
    help = 'Siembra las tarjetas iniciales (Level 0 y 1 del CSV del repo) si la tabla está vacía.'

    def handle(self, *args, **options):
        # Runs on every start: never touch a database that already has cards,
        # or a restart would bring back items an admin deleted.
        if Card.objects.exists():
            self.stdout.write('Ya hay tarjetas, no se siembra nada.')
            return
        if not INITIAL_CSV.exists():
            self.stdout.write(self.style.WARNING(
                f'No existe {INITIAL_CSV.name}; sube un CSV desde el admin.'
            ))
            return
        result = import_cards(INITIAL_CSV.read_text(encoding='utf-8-sig'))
        self.stdout.write(self.style.SUCCESS(f'Tarjetas iniciales: {result}.'))
