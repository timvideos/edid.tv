#!/bin/sh

python manage.py migrate
python manage.py loaddata site.json
python manage.py loaddata manufacturer.json
uwsgi --module=wsgi:application --socket=0.0.0.0:8000 --master --pidfile=/run/uwsgi.pid --static-map /static/img=/opt/edidtv/img --static-map /static/js=/opt/edidtv/js --static-map /static/css=/opt/edidtv/css
