# AI Coding Agent: Real-Time Kafka-to-Redis Pipeline Orchestrator

A full-stack, agent-driven platform that enables users to deploy real-time data pipelines using **Kafka**, **Redis**, **Docker**, and **Kubernetes**—all orchestrated from an intuitive **Streamlit** web UI.

---

## 🚀 Program Summary

This application allows you to:

- Select a Kafka topic (or upload a CSV file) via a web interface.
- Automatically verify Kafka and Redis connectivity.
- Build and deploy a Dockerized Kafka consumer agent to Kubernetes.
- Consume and process events in real time, storing per-video view counts in Redis.
- Visualize live counts in the UI.

---

## ⚡️ Quickstart & Architecture

### 1. Initial Installation

```bash
./install.sh
```

This will:

- Create a virtual environment (`aigenv`) if not present
- Install all required Python dependencies from `requirements.txt`
- Create a `.env` file (if missing) from `.env_sample`

---

### 2. Launch Everything

```bash
./start.sh
```

This will:

- Auto-detect and populate your system’s IP in the `.env` file
- Start Kafka, Redis, and Kubernetes (k3s) locally (if needed)
- Deploy a default Kafka topic and load the consumer agent image
- Launch the Streamlit UI

> ⚠️ **Note:** On the first deployment only, you may need to click **"Build & Deploy"** a second time after the container is created. This is a one-time sync issue.

---

### 3. Infrastructure Options

**Out-of-the-Box (Default):**  
This project provides Docker Compose files for Kafka and Redis, and a Docker-based k3s Kubernetes cluster. You can run everything locally without any external dependencies.

**Bring Your Own Infrastructure:**  
If you already have Kafka, Redis, or Kubernetes running elsewhere:
- Set the appropriate host and port values in your `.env` file
- `start.sh` will detect your running infrastructure and skip starting local containers

---

### 4. Directory Structure for Provided Docker Infrastructure

> **Note:** This applies only if you're using the included Kafka/Redis/k3s setup.

```
agent_deployment/
├── kafka/
│   ├── docker-compose.yml    # Kafka cluster setup
│   └── kafka_setup.py        # Topic initialization
├── redis/
│   └── docker-compose.yml    # Redis standalone setup
└── k3s.yaml                  # Kubernetes config (generated)
agent_kafka/
└── Dockerfile                # Consumer image template
start.sh                      # Main deployment script
.env                          # Your environment config
```

---

### 5. How Startup Works

- `start.sh` checks for `.env`, virtualenv, and infrastructure readiness
- Starts Kafka, Redis, and k3s (if needed)
- Creates Kafka topic and builds the consumer image
- Loads the image into the local Kubernetes cluster
- Launches the Streamlit UI for interactive control

---

## 🛠️ Workflow Overview

### 1. User Input via UI

- The user provides a Kafka topic name (or uploads a file) in the Streamlit web interface

### 2. Pre-deployment Checks

- Kafka and Redis connectivity and configuration are verified

### 3. Agent Generation and Deployment

- A Docker container is built with a Kafka consumer agent
- The container is deployed to Kubernetes using the Python client

### 4. Real-Time Data Processing

- The agent:
  - Subscribes to the topic
  - Consumes messages
  - Updates Redis using `video_views:{topic}:{video_id}` keys

### 5. Monitoring and Visualization

- The UI shows deployment status and live video view counts pulled from Redis

### 6. Self-Service, Automated, and Extensible

- The pipeline is fully managed from the UI and designed for easy customization

---

## 🧰 Key Technologies Used

- **Apache Kafka** — Real-time event streaming
- **Redis** — Fast in-memory storage
- **Docker** — Agent containerization
- **Kubernetes (k3s)** — Lightweight orchestrator
- **Streamlit** — Web-based control UI
- **Python** — Backend logic

---

## 💡 What Makes It Powerful

- **No manual steps**: Just run `./install.sh` then `./start.sh`
- **Live monitoring**: Real-time stream ingestion + visualization
- **Fully pluggable**: Bring your own infra or use the default stack
- **Easily extendable**: Swap Redis, change agent logic, or deploy to cloud clusters

---

## 📦 Getting Started

### Prerequisites

- Python 3.9+
- [Docker](https://docs.docker.com/get-docker/)
- [k3s](https://k3s.io/) (runs inside Docker)
- [Kafka](https://kafka.apache.org/)
- [Redis](https://redis.io/)
- [Streamlit](https://streamlit.io/)

---

### Running the Platform

```bash
./install.sh
./start.sh
```

This will:
- Set up everything (env, dependencies, infra)
- Launch the web UI at [http://localhost:8501](http://localhost:8501)

---

## 🖥️ Usage

1. Visit [http://localhost:8501](http://localhost:8501)
2. Enter a Kafka topic name or upload a CSV
3. Click **"Build & Deploy"**
4. Wait for the deployment to complete (click twice only on first run)
5. See live view counts appear in the table

---

## 📊 Example Output

| Video ID | View Count |
|----------|-----------:|
| video_1  |          1 |
| video_2  |          1 |

---

## 📊 Redis Data Structure

```
HGETALL video_views
# Returns: { "video_1": "count", "video_2": "count", ... }
```

---

## 🧩 Extending the Platform

- Swap Redis with Cassandra or PostgreSQL
- Extend consumer agent logic
- Add support for multiple topics or routing rules
- Deploy to GKE, EKS, or AKS using your kubeconfig

---

## 📄 License

[MIT License](LICENSE)

---

## 🤝 Contributing

Contributions are welcome!  
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

**Build your real-time pipeline. Deploy in seconds. Monitor with ease.**

—  
For help, open an issue or contact the maintainer.

