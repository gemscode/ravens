#!/bin/bash

K3S_SERVER_NAME="k3s-server"
K3S_NETWORK="k3s-net"
K3S_DATA_VOL="k3s-data"
K3S_IMAGE="rancher/k3s:v1.29.5-k3s1"

setup_k8s() {
    # Create Docker network if not exists
    if ! docker network ls | grep -q "$K3S_NETWORK"; then
        echo "Creating Docker network: $K3S_NETWORK"
        docker network create $K3S_NETWORK
    fi

    # Create Docker volume if not exists
    if ! docker volume ls | grep -q "$K3S_DATA_VOL"; then
        echo "Creating Docker volume: $K3S_DATA_VOL"
        docker volume create $K3S_DATA_VOL
    fi

    # Start k3s server if not running
    if ! docker ps | grep -q "$K3S_SERVER_NAME"; then
        if docker ps -a | grep -q "$K3S_SERVER_NAME"; then
            echo "Removing old k3s server container"
            docker rm "$K3S_SERVER_NAME"
        fi
        echo "Starting k3s server container"
        docker run -d --name $K3S_SERVER_NAME \
            --privileged \
            -p 6443:6443 \
            -v $K3S_DATA_VOL:/var/lib/rancher/k3s \
            --network $K3S_NETWORK \
            --hostname $K3S_SERVER_NAME \
            $K3S_IMAGE server --node-name $K3S_SERVER_NAME
    else
        echo "k3s server is already running"
    fi

    # Wait for k3s to be ready
    echo "Waiting for k3s API to be ready..."
    until docker exec $K3S_SERVER_NAME kubectl get nodes &>/dev/null; do
        sleep 2
        echo "Waiting..."
    done

    # Copy kubeconfig to host
    docker cp $K3S_SERVER_NAME:/etc/rancher/k3s/k3s.yaml agent_deployment/k3s.yaml
    sed -i 's/127.0.0.1/host.docker.internal/g' agent_deployment/k3s.yaml

    echo "K3s cluster is ready!"
}

