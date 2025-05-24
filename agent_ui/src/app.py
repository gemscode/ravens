import streamlit as st
import pandas as pd
import subprocess
import psutil
import time
from redis.cluster import RedisCluster
from redis import Redis
from kafka import KafkaAdminClient
from kafka.errors import KafkaError
from kubernetes import client as k8s_client, config as k8s_config
from agent_core.interfaces.config import AppConfig
from agent_core.shared_utils.data import validate_file_format, process_events
from agent_kafka.src.consumer import KafkaStreamProcessor
from agent_kubernetes.src.deployer import deploy_to_kubernetes
from agent_redis.src.client import RedisClient

# Helper to get Docker host address (works for Mac/Windows)
def get_docker_host():
    # For Linux, you may need to use 'localhost' or your host IP
    return "host.docker.internal"

# Basic UI Setup
st.set_page_config(page_title="AI Coding Agent", layout="wide")

# Docker Control Functions
def is_docker_running():
    """Check if Docker daemon is running"""
    try:
        return any("docker" in p.name() for p in psutil.process_iter())
    except Exception:
        return False

def start_local_infra():
    """Start Kafka and Redis using docker-compose"""
    compose_path = "agent_deployment/docker-compose.yml"
    try:
        result = subprocess.run(
            ["docker-compose", "-f", compose_path, "up", "-d"],
            check=True,
            capture_output=True,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error starting Docker: {e.stderr}"

# Enhanced Connection Checkers
class RedisChecker:
    def __init__(self, config, use_local=False):
        self.use_local = use_local
        self.client = None
        
        try:
            if self.use_local:
                # Connect to local Docker Redis (non-cluster)
                self.client = Redis(
                    host=config.redis_host,
                    port=config.redis_port,
                    decode_responses=True
                )
            else:
                # Use configured Redis cluster
                self.client = RedisCluster(
                    startup_nodes=config.redis_nodes,
                    decode_responses=True
                )
            self.client.ping()
        except Exception as e:
            st.error(f"Redis connection error: {str(e)}")

    def is_connected(self):
        try:
            return self.client.ping() if self.client else False
        except Exception as e:
            st.error(f"Redis connection failed: {str(e)}")
            return False


class KafkaChecker:
    def __init__(self, config, use_local_docker=False):
        self.use_local = use_local_docker
        # Force 127.0.0.1 for local connections
        self.bootstrap_servers = "127.0.0.1:9092" if use_local_docker else config.kafka_bootstrap_servers
        self.request_timeout = 10000  # 10 seconds
        
    def topic_exists(self, topic):
        admin_client = None
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                request_timeout_ms=self.request_timeout
            )
            
            # Directly list topics to force connection check
            topics = admin_client.list_topics()
            return topic in topics
            
        except (NoBrokersAvailable, NetworkError) as e:
            st.error(f"Kafka connection failed: {str(e)}")
            return False
        except KafkaError as e:
            st.error(f"Kafka error: {str(e)}")
            return False
        finally:
            if admin_client:
                admin_client.close()
# UI Components
with st.sidebar:
    st.header("Environment Configuration")
    
    # Docker Controls
    use_local_docker = st.checkbox("Use Local Docker Infrastructure", value=True)  # Default to True
    
    if use_local_docker:
        docker_status = "🟢 Running" if is_docker_running() else "🔴 Stopped"
        st.markdown(f"Docker Status: {docker_status}")
        
        if st.button("Start Local Infrastructure", disabled=is_docker_running()):
            with st.status("Starting local services..."):
                success, message = start_local_infra()
                if success:
                    st.success("Local infrastructure started!")
                    st.code(message)
                else:
                    st.error(f"Failed to start: {message}")

    # Data Source Selection
    st.header("Data Configuration")
    data_source = st.radio(
        "Data Source",
        ["File Upload", "Kafka Stream"],
        index=1  # Default to Kafka
    )
    
    if data_source == "Kafka Stream":
        kafka_topic = st.text_input(
            "Kafka Topic",
            value="videos-views"  # Default stream
        )

# Main Interface
st.markdown("""
<div style='border:2px solid #e6e6e6; padding:20px; border-radius:10px'>
    <h1 style='color:#1f77b4'>AI Coding Agent</h1>
    <p>From Prompt to Live Application</p>
</div>
""", unsafe_allow_html=True)

if st.button("Build & Deploy"):
    config = AppConfig()
    
    with st.status("Initializing Deployment...", expanded=True) as status:
        # Initialize checkers with environment config
        redis_checker = RedisChecker(config, use_local_docker)
        kafka_checker = KafkaChecker(config, use_local_docker)
        
        # Connection checks
        st.write("🔌 Checking Redis connection...")
        if not redis_checker.is_connected():
            st.error("Redis connection failed!")
            st.stop()
        st.success("Redis connection verified!")
        
        if data_source == "Kafka Stream":
            st.write("📡 Checking Kafka connection...")
            if not kafka_topic:
                st.error("Please specify a Kafka topic!")
                st.stop()
                
            if not kafka_checker.topic_exists(kafka_topic):
                st.error(f"Kafka topic '{kafka_topic}' not found!")
                st.stop()
            st.success("Kafka topic verified!")
    
    # Deployment Process
    with st.status("Deployment Progress", expanded=True) as status:
        try:
            if data_source == "File Upload":
                uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
                if not validate_file_format(uploaded_file):
                    st.error("Invalid file format!")
                    st.stop()
                results = process_events(uploaded_file, config)
            else:
                st.write(f"🚀 Deploying Kafka Consumer for topic: {kafka_topic}")
                
                # Deploy to Kubernetes with environment awareness
                deployment_name = deploy_to_kubernetes(
                    topic=kafka_topic,
                    use_local_infra=use_local_docker
                )
                
                # Wait for deployment
                st.write("⏳ Waiting for worker deployment...")
                try:
                    k8s_config.load_kube_config()
                except:
                    k8s_config.load_incluster_config()
                
                apps_v1_api = k8s_client.AppsV1Api()
                
                max_retries = 10
                for i in range(max_retries):
                    try:
                        deployment = apps_v1_api.read_namespaced_deployment(
                            name=deployment_name,
                            namespace="default"
                        )
                        if deployment.status.available_replicas == 1:
                            break
                        time.sleep(2)
                    except Exception as e:
                        if i == max_retries - 1:
                            raise Exception(f"Deployment not ready: {str(e)}")
                        time.sleep(2)
                
                # Get results
                st.write(f"📊 Retrieving view counts for topic {kafka_topic}...")
                redis_client = RedisClient(config, use_local_docker)
                view_counts = redis_client.get_video_views(kafka_topic)
                
                # Display results
                st.success("Deployment completed!")
                if view_counts:
                    df = pd.DataFrame(
                        list(view_counts.items()),
                        columns=["Video ID", "View Count"]
                    )
                    st.dataframe(df)
                else:
                    st.info("No view counts found yet. The consumer may still be processing messages.")
            
        except Exception as e:
            st.error(f"Deployment failed: {str(e)}")

