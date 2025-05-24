#!/bin/bash
set -eo pipefail

# Load environment
export $(grep -v '^#' .env | xargs)

GIT_ROOT=$(git rev-parse --show-toplevel)
cd "$GIT_ROOT"

setup_kafka_topic() {
    echo "Running Kafka topic setup..."
    (cd agent_deployment/kafka && \
        KAFKA_BOOTSTRAP_SERVERS="${KAFKA_HOST}:9092" \
        SETUP_TOPIC="videos-views" \
        python setup_helper.py)
}

# --------------------------------------------------
# Service Check Functions
# --------------------------------------------------
check_kafka() {
    docker ps --format '{{.Names}}' | grep -q "^kafka$" && \
    docker exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --list &>/dev/null
}

check_redis() {
    docker ps --format '{{.Names}}' | grep -q "^redis$" && \
    redis-cli -h "$REDIS_HOST" -p 6379 ping &>/dev/null
}

check_k3s() {
    docker ps --format '{{.Names}}' | grep -q "^k3s-server$" && \
    kubectl --kubeconfig=agent_deployment/k3s.yaml get nodes &>/dev/null
}

# --------------------------------------------------
# Service Start Functions
# --------------------------------------------------
start_kafka() {
    if ! check_kafka; then
        echo "Starting Kafka..."
        (cd agent_deployment/kafka && docker compose --env-file ../../.env up -d)
        echo "Waiting for Kafka to be ready..."
        until docker exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --list &>/dev/null; do sleep 2; done
    else
        echo "Kafka already running."
    fi
}

start_redis() {
    if ! check_redis; then
        echo "Starting Redis..."
        (cd agent_deployment/redis && docker compose --env-file ../../.env up -d)
        echo "Waiting for Redis to be ready..."
        until redis-cli -h "$REDIS_HOST" -p 6379 ping &>/dev/null; do sleep 1; done
    else
        echo "Redis already running."
    fi
}

start_k3s() {
    local K3S_PORT=${K3S_PORT:-6444}
    local K3S_HOST=${K3S_HOST:-127.0.0.1}
    local CONTAINER_NAME="k3s-server"

    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        if [ "$(docker inspect -f '{{.State.Running}}' ${CONTAINER_NAME})" = "false" ]; then
            echo "Starting existing k3s-server container..."
            docker start "${CONTAINER_NAME}"
        else
            echo "k3s-server already running."
        fi
    else
        echo "Creating new k3s-server..."
        docker network create k3s-net 2>/dev/null || true
        docker volume create k3s-data 2>/dev/null || true
        docker run -d \
            --name "${CONTAINER_NAME}" \
            --privileged \
            -p ${K3S_PORT}:${K3S_PORT} \
            -v k3s-data:/var/lib/rancher/k3s \
            --network k3s-net \
            rancher/k3s:v1.29.5-k3s1 server \
            --node-name k3s-server \
            --tls-san 192.168.2.200 \
            --https-listen-port ${K3S_PORT}
    fi

    echo "Waiting for k3s to become ready..."
    until docker exec k3s-server kubectl get nodes &>/dev/null; do sleep 2; done

    echo "Generating kubeconfig..."
    docker cp k3s-server:/etc/rancher/k3s/k3s.yaml agent_deployment/k3s.yaml
    sed -i "s/127.0.0.1/${K3S_HOST}/g; s/6443/${K3S_PORT}/g" agent_deployment/k3s.yaml
    kubectl config --kubeconfig=agent_deployment/k3s.yaml rename-context default k3s-context || true
    export KUBECONFIG="${PWD}/agent_deployment/k3s.yaml"
}

# --------------------------------------------------
# Deployment Functions
# --------------------------------------------------
deploy_consumer() {
    echo "Deploying Kafka consumer..."
    docker build -t kafka-consumer:latest -f agent_kafka/Dockerfile .
    docker save kafka-consumer:latest | docker exec -i k3s-server ctr images import -
}

start_ui() {
    echo "All services ready. Starting Streamlit UI..."
    streamlit run agent_ui/src/app.py
}

# --------------------------------------------------
# Main Execution Flow
# --------------------------------------------------
main() {
    # Check Docker availability
    if ! command -v docker &>/dev/null; then
        echo "Error: Docker not found!"
        exit 1
    fi
    docker info &>/dev/null || { 
        echo "Starting Docker..."
        sudo systemctl start docker
        sleep 5
    }

    # Start services
    start_kafka
    start_redis
    start_k3s

    # Add topic setup 
    setup_kafka_topic

    # Deploy consumer
    deploy_consumer

    # Start UI (always last)
    start_ui
}

# Start the main process
main "$@"

