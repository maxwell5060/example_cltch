FROM python:3.7

COPY ./deploy/requirements.txt /var/www/requirements.txt

RUN pip install -r /var/www/requirements.txt

ENV PYTHONPATH /var/www

WORKDIR /var/www
