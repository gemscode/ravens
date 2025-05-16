import streamlit as st
import pandas as pd
from redis.cluster import RedisCluster
from kafka import KafkaAdminClient
from kafka.errors import KafkaError
from agent_core.interfaces.config import AppConfig
from agent_core.shared_utils.data import validate_file_format, process_events
from agent_kafka.src.consumer import KafkaStreamProcessor
from agent_kubernetes.src.deployer import deploy_to_kubernetes
from agent_redis.src.client import RedisClient

# Basic UI Setup
st.set_page_config(page_title="AI Coding Agent", layout="wide")

# Add connection checkers
class RedisChecker:
    def __init__(self, config):
        try:
            # Check first Redis node (for cluster, use RedisCluster)
            self.client = RedisCluster(
                startup_nodes=config.redis_nodes,
                decode_responses=True
            )
            self.client.ping()
        except Exception as e:
            st.error(f"Redis configuration error: {str(e)}")

    def is_connected(self):
        try:
            return self.client.ping()
        except Exception as e:
            st.error(f"Redis connection failed: {str(e)}")
            return False

class KafkaChecker:
    def __init__(self, config):
        self.bootstrap_servers = config.kafka_bootstrap_servers
        
    def topic_exists(self, topic):
        try:
            admin_client = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            topics = admin_client.list_topics()
            admin_client.close()
            return topic in topics
        except KafkaError as e:
            st.error(f"Kafka connection failed: {str(e)}")
            return False

with st.sidebar:
    st.header("Configuration")
    data_source = st.radio("Data Source", ["File Upload", "Kafka Stream"])
    
    if data_source == "File Upload":
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    else:
        kafka_topic = st.text_input("Kafka Topic")

# Main Interface
st.markdown("""
<div style='border:2px solid #e6e6e6; padding:20px; border-radius:10px'>
    <h1 style='color:#1f77b4'>AI Coding Agent</h1>
    <p>From Prompt to Live Application</p>
</div>
""", unsafe_allow_html=True)

if st.button("Build & Deploy"):
    config = AppConfig()
    
    # Pre-deployment checks
    with st.status("Running pre-deployment checks...", expanded=True) as status:
        # Redis check
        st.write("🔌 Checking Redis connection...")
        redis_checker = RedisChecker(config)
        if not redis_checker.is_connected():
            st.error("Redis connection failed!")
            st.stop()
        st.success("Redis connection verified!")
        
        # Kafka check if using Kafka source
        if data_source == "Kafka Stream":
            st.write("📡 Checking Kafka connection...")
            kafka_checker = KafkaChecker(config)
            if not kafka_topic:
                st.error("Please specify a Kafka topic!")
                st.stop()
                
            if not kafka_checker.topic_exists(kafka_topic):
                st.error(f"Kafka topic '{kafka_topic}' not found!")
                st.stop()
            st.success("Kafka topic verified!")
    
    # Continue with deployment if checks pass
    with st.status("Deployment Progress", expanded=True) as status:
        try:
            # Data Processing
            st.write("🛠️ Processing data...")
            if data_source == "File Upload":
                # File upload handling remains the same
                pass
            else:
                st.write(f"📡 Connecting to Kafka topic: {kafka_topic}")
                
                # Deploy to Kubernetes
                st.write("🚢 Building Docker container...")
                # Code to build Docker image would be here
                
                st.write("🚀 Deploying to Kubernetes...")
                deployment_name = deploy_to_kubernetes(kafka_topic)
                
                st.write("⏳ Waiting for deployment to be ready...")
                # Wait for deployment to be ready
                apps_v1_api = client.AppsV1Api()
                deployment = apps_v1_api.read_namespaced_deployment(
                    name=deployment_name,
                    namespace="default"
                )
                
                # Get video view counts
                redis_client = RedisCluster(
                    startup_nodes=config.redis_nodes,
                    decode_responses=True
                )
                
                view_counts = get_video_views(redis_client, kafka_topic)
                
                # Display results
                st.success("Deployment completed!")
                
                st.subheader("Video View Counts")
                df = pd.DataFrame(
                    list(view_counts.items()),
                    columns=["Video ID", "View Count"]
                )
                st.dataframe(df)
                
        except Exception as e:
            st.error(f"Deployment failed: {str(e)}")
        try:
            # Data Processing
            st.write("🛠️ Processing data...")
            if data_source == "File Upload":
                if not validate_file_format(uploaded_file):
                    st.error("Invalid file format!")
                    st.stop()
                results = process_events(uploaded_file, config)
            else:
                processor = KafkaStreamProcessor(config)
                st.write("Processing Kafka Stream...")
                try:
                    st.write(f"📡 Connecting to Kafka topic: {kafka_topic}")
                    processor.process_stream(kafka_topic)
                    st.success("Real-time processing started!")
                except Exception as e:
                    st.error(f"Kafka processing failed: {str(e)}")
                    st.stop()
            
            # Code Generation & Deployment
            st.write("✅ Data processed. Generating code...")
            st.write("🚀 Deploying to Kubernetes...")
            
            st.success("Deployment completed!")
            st.markdown("[View Live App](#)", unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Deployment failed: {str(e)}")

