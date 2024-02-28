FROM python:3.10-alpine3.19

RUN apk update && apk add libpq-dev gcc python3-dev musl-dev libffi-dev

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt


WORKDIR /app
COPY ./ /app/
