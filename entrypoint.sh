#!/bin/bash

while ! nc -z db 5432; do
  sleep 0.5
done

python manage.py migrate
python manage.py runserver 0.0.0.0:8001
