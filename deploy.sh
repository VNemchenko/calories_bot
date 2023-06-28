#!/bin/bash

CONTAINER_NAME=calories_bot

# Останавливаем и удаляем контейнер, если он существует
if [ $(docker ps -a -q -f name=$CONTAINER_NAME) ]; then
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

docker build -t $CONTAINER_NAME .
docker run --env-file .env -d --restart unless-stopped --name $CONTAINER_NAME -v /var/log/my_logs:/app/logs $CONTAINER_NAME

