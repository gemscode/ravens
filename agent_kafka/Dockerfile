# agent_kafka/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/agent_kafka
COPY ../agent_core /app/agent_core
COPY ../agent_redis /app/agent_redis

# Set environment variables
ENV PYTHONPATH=/app

CMD ["python", "-m", "agent_kafka.src.consumer"]

