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

### 1. Environment Configuration

Before running anything, create or edit a `.env` file in the project root with your desired host and port settings:

```
KAFKA_HOST=192.168.2.200
REDIS_HOST=192.168.2.200
K3S_HOST=192.168.2.200
K3S_PORT=6444
```

---

### 2. Infrastructure Options

**Out-of-the-Box (Default):**  
This project provides Docker Compose files for Kafka and Redis, and a Docker-based k3s Kubernetes cluster. You can run everything locally without any external dependencies.

**Bring Your Own Infrastructure:**  
If you already have Kafka, Redis, or Kubernetes running elsewhere, you do **not** need to use the provided Docker Compose files or the k3s Docker setup.  
- Set the appropriate host and port values in your `.env` file.
- The `start.sh` script will detect your running infrastructure and skip starting local containers.

---

### 3. Directory Structure for Provided Docker Infrastructure

> **Note:**  
> The following directory structure is **only relevant if you use the out-of-the-box Docker infrastructure**.  
> This is **not** the project root tree.

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

### 4. How Startup Works

- If you use the provided Docker Compose and k3s Docker setup, `start.sh` will:
  - Start Kafka, Redis, and k3s if they are not already running.
  - Create the Kafka topic if missing.
  - Build and load the Kafka consumer image into k3s.
  - Launch the Streamlit UI.

- If you have your own infrastructure, `start.sh` will:
  - Detect your running services (based on `.env`).
  - Skip starting local containers.
  - Only build/load the consumer image and start the UI.

---

## 🛠️ Workflow Overview

### 1. User Input via UI

- The user provides a Kafka topic name (or uploads a file) in the Streamlit web interface.

### 2. Pre-deployment Checks

- The app verifies connectivity to both Kafka (topic existence) and Redis (cluster health).

### 3. Agent Generation and Deployment

Upon user action, the app:

- **Builds a Docker container** containing a Kafka consumer agent, configured to consume from the specified Kafka topic and write view counts to Redis.
- **Deploys the container to Kubernetes** as a pod (or deployment) using the Kubernetes Python client.

### 4. Real-Time Data Processing

- The deployed Kafka consumer agent:
  - Subscribes to the specified Kafka topic.
  - Consumes messages (e.g., video view events) in real time.
  - Updates per-video view counts in Redis using a key structure like `video_views:{topic}:{video_id}`.

### 5. Monitoring and Visualization

- The Streamlit app:
  - Monitors the Kubernetes deployment status.
  - Once the consumer is running, queries Redis for the current view counts for the given topic.
  - Displays the live counts in the UI as a table for user inspection.

### 6. Self-Service, Automated, and Extensible

- The entire process—from topic selection to deployment and monitoring—is automated and repeatable via the UI.
- The architecture is modular: you can adapt it for other event types, data sinks, or cloud environments.

---

## 🧰 Key Technologies Used

- **Apache Kafka**: For scalable, durable message streaming.
- **Redis**: For fast, scalable, in-memory view count storage.
- **Docker**: To containerize the Kafka consumer agent for portability and reproducibility.
- **Kubernetes (k3s)**: For orchestrating and scaling consumer agents as pods/deployments.
- **Streamlit**: For the interactive web UI that ties the workflow together.
- **Python**: For backend logic and integration.

---

## 💡 What Makes It Powerful

- **Automated Agent Deployment**: The system doesn’t just process data—it dynamically builds, deploys, and manages the agents that do the work, all from a single UI.
- **Real-Time Feedback Loop**: Users see live updates on view counts as soon as the consumer is deployed and running.
- **Cloud-Native, Modular Design**: Easily extensible for new topics, data sources, or output sinks, and ready for production-scale workloads.

---

## 📦 Getting Started

### Prerequisites

- Python 3.9+
- [Docker](https://docs.docker.com/get-docker/)
- [k3s](https://k3s.io/) (runs in Docker, started by `start.sh`)
- [Kafka](https://kafka.apache.org/) (Docker Compose included)
- [Redis](https://redis.io/) (Docker Compose included)
- [Streamlit](https://streamlit.io/)

### Installation

```bash
git clone https://github.com/yourusername/ai-coding-agent.git
cd ai-coding-agent

# Install Python dependencies
pip install -r requirements.txt
```

---

### Running the Infrastructure and UI

```bash
# 1. Ensure .env is configured as shown above
# 2. Start all infrastructure and UI
./start.sh
```

- This will:
  - Start Kafka, Redis, and k3s (if not already running)
  - Create the Kafka topic if missing
  - Build and load the consumer image into k3s
  - Launch the Streamlit UI

---

### Normal Operation

- **Access the UI** at [http://localhost:8501](http://localhost:8501)
- **Deploy the consumer** for a topic using the UI (this is the only step that is repeated per topic)
- **View live counts** as they are processed and stored in Redis

---

## 🖥️ Usage

1. **Access the Streamlit UI** at `localhost:8501`.
2. **Enter a Kafka topic name** (or upload a CSV file).
3. **Click "Build & Deploy"** to launch the pipeline.
4. **Monitor deployment progress** in real time.
5. **View live video view counts** in the results table.

---

## 📊 Example Output

| Video ID | View Count |
|----------|-----------:|
| video_1  |          1 |
| video_2  |          1 |

---

## 📊 Redis Data Structure

The consumer writes view counts to a single Redis hash:

```
HGETALL video_views
# Returns: { "video_1": "count", "video_2": "count", ... }
```

---

## 🧩 Extending the Platform

- Swap Redis for another database.
- Add new data sources or sinks.
- Extend processing logic for new event types.
- Integrate with cloud-native CI/CD pipelines.

---

## 📄 License

[MIT License](LICENSE)

---

## 🤝 Contributing

Contributions are welcome!  
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

**Enjoy building real-time, cloud-native data pipelines with ease!**

---

*For questions or support, open an issue or contact the maintainer.*
