FROM python:3.7-alpine

RUN wget -O /bin/wait-for https://raw.githubusercontent.com/eficode/wait-for/master/wait-for
RUN chmod +x /bin/wait-for
RUN mkdir -p /opt/edidtv/private
WORKDIR /opt/edidtv
ADD *.py requirements.txt docker/entrypoint.sh ./
ADD frontend ./frontend
ADD edid_parser ./edid_parser
ADD templates ./templates
ADD private/__init__.py ./private/
RUN apk add gcc libxslt libxslt-dev libxml2 libxml2-dev libc-dev linux-headers mariadb-connector-c-dev
RUN pip install -r requirements.txt
RUN python manage.py collectstatic --noinput
ENTRYPOINT /bin/sh entrypoint.sh