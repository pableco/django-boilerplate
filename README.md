# Card Sorting — prueba de ordenación de menú

App Django para hacer un **open card sort**: los participantes agrupan las
funciones del back office en categorías que ellos mismos crean y nombran.

Un único servicio: Django + SQLite en un volumen. Sin base de datos externa.

## Pantallas

| Ruta | Quién | Qué |
|---|---|---|
| `/inicio/` | Participantes | Entrada a la prueba (comparte este enlace) |
| `/admin/` | Staff | Gestión de tarjetas, importación de CSV, sesiones |
| `/resultados/` | Staff | Pares más agrupados, agrupaciones por tarjeta, sesiones |

## Desplegar en Railway

1. **New Project → Deploy from GitHub repo**, rama `main`.
2. En el servicio: **Settings → Volumes → Add volume**, montado en `/data`.
   Sin volumen la base de datos se borra en cada deploy.
3. **Variables**:

   | Variable | Valor |
   |---|---|
   | `SECRET_KEY` | una clave larga aleatoria |
   | `DEBUG` | `False` |
   | `DJANGO_SUPERUSER_USERNAME` | `admin` |
   | `DJANGO_SUPERUSER_PASSWORD` | la contraseña del admin |

   No hacen falta `DATABASE_URL`, `ALLOWED_HOSTS` ni `CSRF_TRUSTED_ORIGINS`:
   la ruta del volumen y el dominio los pone Railway.

Cada arranque ejecuta, en el mismo contenedor: `migrate` → `load_cards`
(solo siembra si no hay tarjetas) → `create_superuser_if_none` →
`collectstatic` → `gunicorn`.

## Tarjetas

- **Iniciales**: `card_sorting/data/initial_items.csv`, se cargan los
  Level 0 y Level 1 la primera vez que la base está vacía.
- **Desde el admin** (*Tarjetas → Importar CSV*): eliges niveles y si
  sustituyes el set actual. Las tarjetas se identifican por `Name`.
- **Retirar vs borrar**: retirar de la prueba conserva los resultados
  ya recogidos; borrar los elimina.

Desde terminal:

```bash
python manage.py import_cards ruta.csv                 # Level 0 y 1
python manage.py import_cards ruta.csv --levels all    # todos los niveles
python manage.py import_cards ruta.csv --replace       # retira lo que no esté
```

## Local

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py load_cards
python manage.py createsuperuser
python manage.py runserver
```
