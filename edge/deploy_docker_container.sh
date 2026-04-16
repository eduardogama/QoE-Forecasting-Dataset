#!/bin/bash

# Docker image to deploy
IMAGE="eduardogama/edge_apache:latest"

# Container name prefix
CONTAINER_NAME_PREFIX="my-container"

# Log file to store the timing results
LOG_FILE="docker_deploy_times.log"

# Clear the log file if it exists
> $LOG_FILE

# Loop to deploy the Docker image 100 times
for i in {1..100}
do
    CONTAINER_NAME="${CONTAINER_NAME_PREFIX}-${i}"
    
    echo "Deploying Docker container: Attempt $i"
    
    # Remove the container if it already exists
    if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
        docker rm -f $CONTAINER_NAME
    fi
    
    # Measure the time taken to deploy the container
    { time docker run -d --name $CONTAINER_NAME $IMAGE; } 2>> $LOG_FILE
    
    echo "----------------------------------------" >> $LOG_FILE
    
    # Stop and remove the container after deployment
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
done

echo "Docker container deployment timing results saved to $LOG_FILE"