#!/bin/bash
set -e
cd /app/backend
python manage.py migrate_schemas --shared
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --config gunicorn.conf.py
