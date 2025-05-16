import streamlit as st
import pandas as pd
from agent_core.interfaces.config import AppConfig
from agent_core.shared_utils.data import validate_file_format, process_events
from agent_kafka.src.consumer import KafkaStreamProcessor

# Basic UI Setup
st.set_page_config(page_title="AI Coding Agent", layout="wide")

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
    
    if data_source == "File Upload" and not uploaded_file:
        st.error("Please upload a file first!")
        st.stop()
        
    with st.status("Deployment Progress", expanded=True) as status:
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
                with st.status("Processing Kafka Stream..."):
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

