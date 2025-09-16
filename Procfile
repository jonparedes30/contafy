release: python manage.py migrate --settings=heroku_settings
web: gunicorn core.wsgi --log-file - --settings=heroku_settings