web: gunicorn composeexample.wsgi --log-file -
release: python manage.py migrate --no-input && python manage.py load_cards
