#!/bin/bash
set -e

# Load environment variables
set -a
source .env 2>/dev/null || true
set +a

# Project-specific cleanup
echo "Starting project cleanup..."

# Clean Kafka
echo "Cleaning Kafka..."
(cd agent_deployment/kafka && docker compose --env-file ../../.env down -v)

# Clean Redis 
echo "Cleaning Redis..."
(cd agent_deployment/redis && docker compose --env-file ../../.env down -v)

# Clean k3s resources
echo "Cleaning k3s resources..."
docker stop k3s-server 2>/dev/null || true
docker rm -f k3s-server 2>/dev/null || true

# Remove project-specific Docker assets
docker network rm k3s-net 2>/dev/null || true
docker volume rm k3s-data 2>/dev/null || true

# Remove setup flags and kubeconfig
echo "Removing state files..."
rm -f agent_deployment/.setup_complete
rm -f agent_deployment/k3s.yaml

# Targeted Docker cleanup (project-specific only)
echo "Cleaning Docker artifacts..."
docker system prune -af --filter "label=io.k3s.project=streaming-demo"

echo "Cleanup complete! Project resources removed while preserving system Docker items."

