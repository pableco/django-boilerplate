# Card Sorting — Prueba de ordenación de menú

Aplicación Django para realizar pruebas de **open card sorting** con usuarios reales.
Permite descubrir cómo los participantes agrupan mentalmente los ítems del menú de una aplicación de back office.

## ¿Qué es un card sort?

Los participantes reciben tarjetas con nombres de funciones del sistema y las agrupan libremente en categorías que ellos mismos crean y nombran. Los resultados revelan el modelo mental de los usuarios y guían la arquitectura de la información del menú.

## Pantallas

| Ruta | Descripción |
|---|---|
| `/` | Redirige a inicio |
| `/inicio/` | Formulario de entrada del participante |
| `/ordenar/<uuid>/` | Interfaz drag-and-drop de ordenación |
| `/done/<uuid>/` | Pantalla de agradecimiento |
| `/resultados/` | Dashboard de resultados (requiere staff) |
| `/admin/` | Panel de administración Django |

---

## Despliegue en Railway (recomendado)

### 1. Crear proyecto

1. Ve a [railway.app](https://railway.app) y crea una cuenta
2. **New Project → Deploy from GitHub repo** → selecciona este repositorio
3. Railway detectará el `Procfile` y usará Nixpacks automáticamente

### 2. Añadir base de datos

En el proyecto de Railway:

1. Haz clic en **+ New** → **Database** → **PostgreSQL**
2. Cuando Railway pregunte si conectarlo al servicio web, acepta
3. Esto inyecta `DATABASE_URL` automáticamente — no necesitas configurarla tú

### 3. Variables de entorno

En el servicio web → pestaña **Variables**, añade:

| Variable | Valor |
|---|---|
| `SECRET_KEY` | Una clave aleatoria (ver abajo cómo generarla) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `tu-app.up.railway.app` (tu dominio de Railway) |

> `CSRF_TRUSTED_ORIGINS` **no hace falta configurarla**: se auto-construye a partir de `ALLOWED_HOSTS`.

**Generar SECRET_KEY** (ejecuta esto en tu terminal local):

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Primer deploy

Railway desplegará automáticamente al guardar las variables. El `Procfile` ejecuta en cada deploy:

```
python manage.py migrate --no-input
python manage.py load_cards          # carga los 40 ítems de menú
gunicorn composeexample.wsgi         # inicia el servidor
```

### 5. Crear superusuario (para ver resultados)

```bash
# Con la CLI de Railway instalada:
railway run python manage.py createsuperuser

# O en el dashboard: Service → Shell
python manage.py createsuperuser
```

### 6. Compartir con participantes

La URL pública de inicio es:

```
https://tu-app.up.railway.app/inicio/
```

Los resultados se ven en:

```
https://tu-app.up.railway.app/resultados/
```

---

## Desarrollo local con Docker

```bash
# Copiar variables de entorno
cp .env.example .env

# Levantar servicios
docker compose up

# En otra terminal: migraciones y datos iniciales
docker compose exec web python manage.py migrate
docker compose exec web python manage.py load_cards
docker compose exec web python manage.py createsuperuser
```

La app queda disponible en `http://localhost:8000`.

## Desarrollo local sin Docker

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables (SQLite para desarrollo rápido)
export DATABASE_URL=sqlite:///db.sqlite3
export SECRET_KEY=dev-key-not-for-production
export DEBUG=True

# Migraciones y datos
python manage.py migrate
python manage.py load_cards
python manage.py createsuperuser

# Servidor
python manage.py runserver
```

---

## Gestión de tarjetas

Las 40 tarjetas pre-cargadas cubren estas áreas de un back office típico:

- Panel principal (Dashboard, Notificaciones)
- Usuarios y acceso (Gestión de Usuarios, Roles, Grupos, Auditoría)
- Clientes y contactos
- Catálogo (Productos, Categorías, Precios, Proveedores)
- Inventario y compras
- Ventas y facturación (Órdenes, Facturas, Cotizaciones, Pagos, Gastos)
- Reportes y analíticas
- Operaciones (Tareas, Calendario, Soporte, Tickets, Mensajes)
- Documentos y contratos
- Configuración del sistema (General, Correo, Integraciones, API Keys, Seguridad, Backup)

### Modificar tarjetas

**Desde el admin** (`/admin/card_sorting/card/`): editar, añadir o desactivar tarjetas individualmente.

**Recargar desde cero**:

```bash
python manage.py load_cards --clear
```

---

## Modelo de datos

```
Card                    — ítem de menú (título, descripción, orden)
SortingSession          — sesión de un participante
  └── Category          — categoría creada por el participante
  └── CardPlacement     — dónde colocó cada tarjeta
```

## Stack

- **Django 4.2 LTS** + PostgreSQL
- **SortableJS** — drag-and-drop sin dependencias de build
- **Bootstrap 5** — estilos y componentes UI
- **Whitenoise** — servir archivos estáticos sin CDN externo
- **Gunicorn** — servidor WSGI de producción
