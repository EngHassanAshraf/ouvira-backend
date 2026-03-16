#!/bin/bash
set -e
cd /app/backend
python manage.py migrate 
python manage.py migrate_schemas
python manage.py migrate_schemas --shared
gunicorn config.wsgi:application --config gunicorn.conf.py
