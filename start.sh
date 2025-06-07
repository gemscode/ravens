#!/bin/bash
set -eo pipefail

export PYTHONPATH="$(pwd):$PYTHONPATH"

GIT_ROOT=$(git rev-parse --show-toplevel)
cd "$GIT_ROOT"

# --------------------------------------------------
# Sanity check: Ensure venv is set up
# --------------------------------------------------
if [ ! -f "aigenv/bin/activate" ]; then
    echo "❌ Virtual environment not found."
    echo "➡️  Please run ./install.sh first to set up your environment."
    exit 1
fi

# Activate venv
source aigenv/bin/activate

# Optional: Verify kafka-python is installed
if ! python -c "import kafka" &>/dev/null; then
    echo "❌ kafka-python not installed."
    echo "➡️  Please re-run ./install.sh to install dependencies."
    exit 1
fi

# --------------------------------------------------
# Auto-update .env with current host IP
# --------------------------------------------------
update_env_file() {
    local ENV_FILE=".env"

    if command -v ip >/dev/null; then
        HOST_IP=$(ip route get 8.8.8.8 | awk '{for(i=1;i<=NF;i++) if ($i=="src") print $(i+1)}' | head -n1)
    else
        HOST_IP=$(ifconfig | grep 'inet ' | grep -v 127.0.0.1 | awk '{print $2}' | head -n1)
    fi
    [ -z "$HOST_IP" ] && HOST_IP="127.0.0.1"

    echo "Updating .env with detected IP: $HOST_IP"

    local keys_values="
KAFKA_HOST=$HOST_IP
KAFKA_BOOTSTRAP_SERVERS=${HOST_IP}:9092
REDIS_HOST=$HOST_IP
redis_host=$HOST_IP
ELASTIC_HOST=http://${HOST_IP}:9200
K3S_HOST=$HOST_IP
K3S_PORT=6444
"

    touch "$ENV_FILE"

    echo "$keys_values" | while IFS= read -r line; do
        key=$(echo "$line" | cut -d= -f1)
        value=$(echo "$line" | cut -d= -f2-)

        if grep -q "^$key=" "$ENV_FILE"; then
            sed -i.bak "s|^$key=.*|$key=$value|" "$ENV_FILE"
        else
            echo "$key=$value" >> "$ENV_FILE"
        fi
    done

    grep -E '^[A-Za-z_][A-Za-z0-9_]*=.*' "$ENV_FILE" > "$ENV_FILE.cleaned"
    mv "$ENV_FILE.cleaned" "$ENV_FILE"
    rm -f "${ENV_FILE}.bak"
}

# --------------------------------------------------
# Safe .env loader
# --------------------------------------------------
load_env() {
    while IFS='=' read -r key value; do
        if [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
            export "$key=$value"
        fi
    done < <(grep -E '^[A-Za-z_][A-Za-z0-9_]*=.*' .env)
}

# --------------------------------------------------
# Kafka Setup
# --------------------------------------------------
setup_kafka_topic() {
    echo "Running Kafka topic setup..."
    (cd agent_deployment/kafka && \
        KAFKA_BOOTSTRAP_SERVERS="${KAFKA_HOST}:9092" \
        SETUP_TOPIC="videos-views" \
        python setup_helper.py)
}

check_kafka() {
    docker ps --format '{{.Names}}' | grep -q "^kafka$" && \
    docker exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --list &>/dev/null
}

check_redis() {
    docker ps --format '{{.Names}}' | grep -q "^redis$" && \
    redis-cli -h "$REDIS_HOST" -p 6379 ping &>/dev/null
}

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

    if command -v ip >/dev/null; then
        HOST_IP=$(ip route get 8.8.8.8 | awk '{for(i=1;i<=NF;i++) if ($i=="src") print $(i+1)}' | head -n1)
    else
        HOST_IP=$(ifconfig | grep 'inet ' | grep -v 127.0.0.1 | awk '{print $2}' | head -n1)
    fi
    [ -z "$HOST_IP" ] && HOST_IP="127.0.0.1"

    echo "Detected HOST_IP: $HOST_IP"
    local K3S_HOST=${K3S_HOST:-$HOST_IP}
    local CONTAINER_NAME="k3s-server"

    if [ -f agent_deployment/k3s.yaml ]; then
        OLD_IP=$(grep 'server: https://' agent_deployment/k3s.yaml | awk -F'//' '{print $2}' | cut -d: -f1)
        if [ "$OLD_IP" != "$K3S_HOST" ]; then
            echo "IP changed from $OLD_IP to $K3S_HOST - recreating cluster..."
            docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
            docker volume rm k3s-data 2>/dev/null || true
            rm -f agent_deployment/k3s.yaml
        fi
    fi

    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        if [ "$(docker inspect -f '{{.State.Running}}' ${CONTAINER_NAME})" = "false" ]; then
            echo "Starting existing k3s-server..."
            docker start "$CONTAINER_NAME"
        else
            echo "k3s-server already running."
        fi
    else
        echo "Creating new k3s-server with IP: $K3S_HOST"
        docker network create k3s-net 2>/dev/null || true
        docker volume create k3s-data 2>/dev/null || true
        docker run -d \
            --name "$CONTAINER_NAME" \
            --privileged \
            -p ${K3S_PORT}:${K3S_PORT} \
            -v k3s-data:/var/lib/rancher/k3s \
            --network k3s-net \
            rancher/k3s:v1.29.5-k3s1 server \
            --node-name k3s-server \
            --tls-san "$K3S_HOST" \
            --tls-san 127.0.0.1 \
            --https-listen-port "$K3S_PORT"
    fi

    echo "Waiting for k3s to become ready..."
    until docker exec k3s-server kubectl get nodes &>/dev/null; do sleep 2; done

    echo "Generating kubeconfig..."
    docker cp k3s-server:/etc/rancher/k3s/k3s.yaml agent_deployment/k3s.yaml

    if sed --version 2>/dev/null | grep -q GNU; then
        sed -i "s|server: https://[^[:space:]]*|server: https://${K3S_HOST}:${K3S_PORT}|g" agent_deployment/k3s.yaml
    else
        sed -i "" "s|server: https://[^[:space:]]*|server: https://${K3S_HOST}:${K3S_PORT}|g" agent_deployment/k3s.yaml
    fi

    kubectl config --kubeconfig=agent_deployment/k3s.yaml rename-context default k3s-context || true
    export KUBECONFIG="${PWD}/agent_deployment/k3s.yaml"
}

deploy_consumer() {
    echo "Deploying Kafka consumer..."
    docker build -t kafka-consumer:latest -f agent_kafka/Dockerfile .
    docker save kafka-consumer:latest | docker exec -i k3s-server ctr images import -
}

start_ui() {
    echo "All services ready. Starting Streamlit UI..."
    streamlit run agent_ui/src/app.py
}

check_docker() {
    if ! command -v docker &>/dev/null; then
        echo "Docker not found. Please install Docker Desktop."
        exit 1
    fi
    if ! docker info &>/dev/null; then
        echo "Docker not running. Launching Docker Desktop..."
        open -a Docker
        while ! docker info &>/dev/null; do
            sleep 2
            echo -n "."
        done
        echo ""
    fi
}

# --------------------------------------------------
# Main Execution
# --------------------------------------------------
main() {
    update_env_file
    load_env

    check_docker
    start_kafka
    start_redis
    start_k3s
    setup_kafka_topic
    deploy_consumer
    start_ui
}

main "$@"

