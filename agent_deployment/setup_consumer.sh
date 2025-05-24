#!/bin/bash

setup_consumer() {
    CONSUMER_IMAGE="kafka-consumer:latest"

    if ! docker images -q "$CONSUMER_IMAGE" &> /dev/null; then
        echo "Building consumer Docker image..."
        docker build -t "$CONSUMER_IMAGE" -f agent_kafka/Dockerfile agent_kafka
        exit_code=$?
        if [ $exit_code -ne 0 ]; then
            echo "Error building consumer image. Exit code: $exit_code"
            exit 1
        fi
        
        # Load image into k3s
        echo "Loading image into k3s cluster..."
        docker save kafka-consumer:latest | docker exec -i k3s-server ctr images import -
    else
        echo "Consumer image exists: $CONSUMER_IMAGE"
    fi
}

