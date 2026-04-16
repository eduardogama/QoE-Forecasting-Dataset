#!/bin/sh

dockerd &

while ! docker info > /dev/null 2>&1; do
    sleep 1
done


echo "Docker has been started"

docker build -t my-apache-server -f /home/app/Dockerfile.apache /home/app
docker run -d -p 80:80 --name apache-container my-apache-server

tail -f /dev/null
