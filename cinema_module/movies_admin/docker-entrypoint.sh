#!/usr/bin/env bash

sleep 10
python create_schema.py
python manage.py compilemessages -l en -l ru
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser --noinput

gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 1