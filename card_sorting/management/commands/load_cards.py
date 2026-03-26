from django.core.management.base import BaseCommand
from card_sorting.models import Card

MENU_ITEMS = [
    # — Panel principal —
    (1,  "Dashboard / Inicio", "Pantalla principal con métricas y resumen del sistema"),
    (2,  "Notificaciones", "Centro de alertas, avisos y mensajes del sistema"),

    # — Usuarios y acceso —
    (3,  "Gestión de Usuarios", "Crear, editar y desactivar cuentas de usuarios"),
    (4,  "Roles y Permisos", "Definir roles y controlar qué puede hacer cada usuario"),
    (5,  "Grupos de Usuarios", "Agrupar usuarios por departamento o función"),
    (6,  "Sesiones Activas", "Ver quién está conectado en este momento"),
    (7,  "Registro de Auditoría", "Historial de acciones realizadas en el sistema"),

    # — Clientes y contactos —
    (8,  "Clientes", "Lista y gestión de clientes registrados"),
    (9,  "Prospectos / Leads", "Clientes potenciales y seguimiento comercial"),
    (10, "Contactos", "Directorio de personas de contacto"),

    # — Catálogo —
    (11, "Productos", "Catálogo de productos o servicios ofrecidos"),
    (12, "Categorías de Productos", "Organización del catálogo por categorías"),
    (13, "Precios y Tarifas", "Configuración de precios, descuentos y tarifas especiales"),
    (14, "Proveedores", "Empresas y personas que suministran productos o servicios"),

    # — Inventario —
    (15, "Inventario", "Stock actual, entradas y salidas de productos"),
    (16, "Almacenes", "Gestión de ubicaciones físicas o depósitos"),
    (17, "Órdenes de Compra", "Solicitudes de compra a proveedores"),

    # — Ventas y facturación —
    (18, "Órdenes de Venta", "Pedidos realizados por los clientes"),
    (19, "Facturas", "Emisión y consulta de facturas electrónicas"),
    (20, "Cotizaciones", "Presupuestos y propuestas enviadas a clientes"),
    (21, "Pagos y Cobros", "Registro de pagos recibidos y pendientes"),
    (22, "Gastos", "Control de gastos operativos y administrativos"),
    (23, "Notas de Crédito", "Devoluciones y ajustes sobre facturas emitidas"),

    # — Reportes y análisis —
    (24, "Reportes Financieros", "Balances, flujo de caja e informes contables"),
    (25, "Estadísticas de Ventas", "Gráficas y métricas del rendimiento comercial"),
    (26, "Analíticas", "Tablero de análisis de datos y tendencias"),
    (27, "Exportar Datos", "Descargar información en Excel, CSV o PDF"),

    # — Operaciones y soporte —
    (28, "Tareas", "Lista de tareas asignadas y pendientes"),
    (29, "Calendario", "Agenda de eventos, citas y recordatorios"),
    (30, "Soporte al Cliente", "Gestión de solicitudes de ayuda de clientes"),
    (31, "Tickets de Soporte", "Registro y seguimiento de incidencias"),
    (32, "Mensajes / Chat", "Comunicación interna entre el equipo"),

    # — Documentos y contratos —
    (33, "Documentos", "Repositorio de archivos y documentos del negocio"),
    (34, "Contratos", "Gestión de contratos con clientes y proveedores"),

    # — Configuración del sistema —
    (35, "Configuración General", "Parámetros globales del sistema"),
    (36, "Configuración de Correo", "Plantillas y servidor de correo electrónico"),
    (37, "Integraciones", "Conexiones con servicios externos y APIs de terceros"),
    (38, "API Keys", "Gestión de claves de acceso programático"),
    (39, "Seguridad", "Contraseñas, 2FA y políticas de acceso"),
    (40, "Backup y Restauración", "Copias de seguridad y recuperación de datos"),
]


class Command(BaseCommand):
    help = 'Carga los ítems del menú de back office como tarjetas de card sorting'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Eliminar todas las tarjetas existentes antes de cargar',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = Card.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Eliminadas {count} tarjetas existentes.'))

        created = 0
        skipped = 0

        for order, title, description in MENU_ITEMS:
            _, is_new = Card.objects.get_or_create(
                title=title,
                defaults={'description': description, 'order': order}
            )
            if is_new:
                created += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Cargados {created} ítems nuevos. '
                f'{skipped} ya existían y fueron omitidos.'
            )
        )
