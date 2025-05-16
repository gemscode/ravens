# AI Coding Agent: Real-Time Kafka-to-Redis Pipeline Orchestrator

A full-stack, agent-driven platform that enables users to deploy real-time data pipelines using **Kafka**, **Redis**, **Docker**, and **Kubernetes**-all orchestrated from an intuitive **Streamlit** web UI.

---

## 🚀 Program Summary

This application allows you to:

- Select a Kafka topic (or upload a CSV file) via a web interface.
- Automatically verify Kafka and Redis connectivity.
- Build and deploy a Dockerized Kafka consumer agent to Kubernetes.
- Consume and process events in real time, storing per-video view counts in Redis.
- Visualize live counts in the UI.

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

- The entire process-from topic selection to deployment and monitoring-is automated and repeatable via the UI.
- The architecture is modular: you can adapt it for other event types, data sinks, or cloud environments.

---

## 🧰 Key Technologies Used

- **Apache Kafka**: For scalable, durable message streaming.
- **Redis Cluster**: For fast, scalable, in-memory view count storage.
- **Docker**: To containerize the Kafka consumer agent for portability and reproducibility.
- **Kubernetes**: For orchestrating and scaling consumer agents as pods/deployments.
- **Streamlit**: For the interactive web UI that ties the workflow together.
- **Python**: For backend logic and integration.

---

## 💡 What Makes It Powerful

- **Automated Agent Deployment**: The system doesn’t just process data-it dynamically builds, deploys, and manages the agents that do the work, all from a single UI.
- **Real-Time Feedback Loop**: Users see live updates on view counts as soon as the consumer is deployed and running.
- **Cloud-Native, Modular Design**: Easily extensible for new topics, data sources, or output sinks, and ready for production-scale workloads.

---

## 📦 Getting Started

### Prerequisites

- Python 3.9+
- [Docker](https://docs.docker.com/get-docker/)
- [Kubernetes](https://kubernetes.io/) cluster (Minikube, K3s, EKS, GKE, etc.)
- [Kafka](https://kafka.apache.org/) cluster (local or cloud)
- [Redis Cluster](https://redis.io/docs/management/scaling/)
- [Streamlit](https://streamlit.io/)

### Installation

```bash
git clone https://github.com/yourusername/ai-coding-agent.git
cd ai-coding-agent

# Install Python dependencies
pip install -r requirements.txt

# (Optional) Build the Kafka consumer Docker image
cd agent_kafka
docker build -t your-registry/kafka-consumer:latest .
```

### Running the App

```bash
# Start the Streamlit UI
streamlit run agent_ui/src/app.py
```

Visit [http://localhost:8501](http://localhost:8501) in your browser.

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
| 0001     |      1,234 |
| 0002     |        567 |

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

