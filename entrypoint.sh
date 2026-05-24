#!/bin/sh
set -e
flask --app app db upgrade
exec gunicorn -w 2 -b 0.0.0.0:8000 app:app
