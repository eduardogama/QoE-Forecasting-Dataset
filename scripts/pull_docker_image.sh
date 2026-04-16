#!/bin/bash

# Docker image to pull
IMAGE="edge_apache"

# Log file to store the timing results
LOG_FILE="docker_pull_times_v2.log"

# Clear the log file if it exists
> $LOG_FILE

# Loop to pull the Docker image 100 times
for i in {1..100}
do
    echo "Pulling Docker image: Attempt $i"

    # Remove the image to force pull from Docker Hub
    docker rmi -f $IMAGE
    
    # Pull the image and store the time taken in the log file
    { time docker pull $IMAGE; } 2>> $LOG_FILE

    echo "----------------------------------------" >> $LOG_FILE
done

echo "Docker image pull timing results saved to $LOG_FILE"