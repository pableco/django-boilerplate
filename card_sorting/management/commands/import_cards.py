from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from card_sorting.importer import DEFAULT_LEVELS, import_cards


class Command(BaseCommand):
    help = 'Importa tarjetas desde un CSV de arquitectura de información.'

    def add_arguments(self, parser):
        parser.add_argument('csv_path')
        parser.add_argument(
            '--levels', default=','.join(DEFAULT_LEVELS),
            help='Niveles a importar separados por coma, o "all" para todos.',
        )
        parser.add_argument(
            '--replace', action='store_true',
            help='Retira de la prueba las tarjetas que no estén en el CSV.',
        )

    def handle(self, csv_path, levels, replace, **options):
        path = Path(csv_path)
        if not path.exists():
            raise CommandError(f'No existe {path}')
        level_list = None if levels == 'all' else [l.strip() for l in levels.split(',') if l.strip()]
        try:
            result = import_cards(path.read_text(encoding='utf-8-sig'), levels=level_list, replace=replace)
        except ValueError as exc:
            raise CommandError(str(exc))
        self.stdout.write(self.style.SUCCESS(str(result)))
