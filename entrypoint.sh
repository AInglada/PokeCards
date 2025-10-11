#!/bin/sh

# Espera a que la base de datos esté lista
if [ "$DATABASE" = "postgres" ]; then
  echo "Esperando a Postgres..."
  while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 0.1
  done
fi

# Migraciones
python manage.py migrate --noinput

# Servidor dev (cambiar a gunicorn en producción)
if [ "$DJANGO_ENV" = "prod" ]; then
  exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
else
  exec python manage.py runserver 0.0.0.0:8000
fi
