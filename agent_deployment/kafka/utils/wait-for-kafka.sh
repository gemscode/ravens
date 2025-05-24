#!/bin/bash

hostport="$1"
shift

host=${hostport%:*}
port=${hostport#*:}

echo "Waiting for Kafka at $host:$port (max 300s)..."

# First check port accessibility
timeout 300 sh -c '
while ! nc -z $0 $1; do
    echo "Kafka port not reachable..."
    sleep 5
done
' "$host" "$port" || {
    echo "Kafka port never became reachable!"
    exit 1
}

# Then check topic listing capability
timeout 60 sh -c '
while ! kafka-topics.sh --bootstrap-server $0:$1 --list >/dev/null 2>&1; do
    echo "Kafka not operational yet..."
    sleep 2
done
' "$host" "$port" || {
    echo "Kafka API never became responsive!"
    exit 1
}

echo "Kafka is fully operational! Executing command: $@"
exec "$@"

