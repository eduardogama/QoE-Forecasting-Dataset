FROM ubuntu:focal

##UPDATE
RUN apt-get update -y

##PYTHON
RUN apt-get install -y \
    python3-pip \
    python3-dev \ 
    docker.io
    
RUN pip3 install --upgrade pip

COPY .env /
COPY requirements.txt /

RUN pip install -r requirements.txt

COPY source/app.py /
COPY source/builder.py /
COPY source/monitoring.py /


CMD [ "python3", "app.py" ]
