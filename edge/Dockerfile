FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    net-tools \
    iputils-ping \
    iproute2

WORKDIR /app

COPY --chown=app:app ./lrucache.py /app/
COPY --chown=app:app ./app.py /app/
COPY --chown=app:app requirements.txt /app/

RUN pip install -r requirements.txt


CMD python app.py
