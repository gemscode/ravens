# agent_ui/src/app.py
import streamlit as st
import os
import time
import json
from datetime import datetime
from kubernetes import client as k8s_client, config as k8s_config
from kubernetes.client.rest import ApiException
from models import ResumeData, ResumeMetadata, ProcessingEvent
from services import BackendService
from components import render_sankey_chart, render_company_summaries, render_education
from agent_core.interfaces.config import AppConfig

# Initialize services and config
config = AppConfig()
backend = BackendService()

# Custom CSS for status indicators
st.markdown("""
<style>
.status-container {
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 0.5rem;
    background-color: #f8f9fa;
}
.status-item {
    display: flex;
    align-items: center;
    margin: 0.5rem 0;
}
.status-icon {
    margin-right: 0.75rem;
    font-size: 1.25rem;
}
</style>
""", unsafe_allow_html=True)

def main_ui():
    st.title("AI Resume Analyzer")
    
    # Sidebar - File Upload and Deployment
    with st.sidebar:
        st.header("Resume Management")
        uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])
        user_id = st.text_input("User ID", help="Enter any unique identifier for your session")
        
        if uploaded_file and user_id:
            handle_file_upload(uploaded_file, user_id)
        
        # Deployment controls
        st.header("Cluster Management")
        if st.button("Build & Deploy Worker", 
                    disabled=not st.session_state.get('ready_to_deploy', False)):
            deploy_kubernetes_worker()

    # Main content area
    if 'user_id' in st.session_state:
        render_processing_tab()
        render_search_tab()

def handle_file_upload(file, user_id):
    try:
        # Save file and calculate checksum
        file_path = save_uploaded_file(file, user_id)
        checksum = backend.calculate_checksum(file_path)
        
        # Check for existing resume with proper status check
        existing_doc = backend.get_resume_document(checksum)
        
        if existing_doc:
            doc_status = existing_doc.get('status', 'unknown')
            
            if doc_status == 'processed':
                st.info("This resume has already been processed")
                st.session_state.resume_data = ResumeData(**existing_doc['processed_data'])
                return True
                
            elif doc_status == 'processing':
                st.warning("Resume is already being processed")
                return False
                
            elif doc_status == 'failed':
                if st.button("Retry Failed Processing"):
                    # Create new event only after user confirmation
                    event = {
                        "file_path": file_path,
                        "checksum": checksum,
                        "user_id": user_id
                    }
                    backend.send_processing_event(event)
                    st.success("Resume re-queued for processing!")
                    return True
                return False
                
        # Create and index metadata (new upload)
        metadata = ResumeMetadata(
            checksum=checksum,
            filename=file.name,
            file_path=file_path,
            user_id=user_id,
            upload_date=datetime.now()
        )
        backend.create_resume_document(metadata)
        
        # Send processing event (only essential fields)
        event = {
            "file_path": file_path,
            "checksum": checksum,
            "user_id": user_id
        }
        backend.send_processing_event(event)
        
        st.session_state.user_id = user_id
        st.session_state.ready_to_deploy = True
        st.success("Resume uploaded and queued for processing!")
        return True

    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
        return False

def handle_file_upload___(file, user_id):
    try:
        # Save file and calculate checksum
        file_path = save_uploaded_file(file, user_id)
        checksum = backend.calculate_checksum(file_path)
        
        # Check for existing resume
        if backend.check_existing_resume(checksum):
            st.info("This resume has already been processed")
            try:
                doc = backend.es.get(index="resumes", id=checksum)["_source"]
                if "processed_data" in doc and doc["processed_data"]:
                    # Parse the processed_data into a ResumeData object
                    st.session_state.resume_data = ResumeData(**doc["processed_data"])
                    st.success("Resume data loaded from previous processing")
                else:
                    st.warning("Resume exists but processing data not found")
            except Exception as e:
                st.error(f"Error fetching resume data: {str(e)}")
                
            st.session_state.ready_to_deploy = True
            return True
            st.session_state.ready_to_deploy = True
            return True
        
        # Create and index metadata
        metadata = ResumeMetadata(
            checksum=checksum,
            filename=file.name,
            file_path=file_path,
            user_id=user_id,
            upload_date=datetime.now()
        )
        backend.index_resume_metadata(metadata)
        
        # Send processing event
        event = ProcessingEvent(
            file_path=file_path,
            checksum=checksum,
            user_id=user_id
        )
        backend.send_processing_event(event)
        
        st.session_state.user_id = user_id
        st.session_state.ready_to_deploy = True
        st.success("Resume uploaded and queued for processing!")
        return True

    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
        return False

def render_processing_tab():
    """Show processing status and analysis results"""
    if 'resume_data' in st.session_state:
        tab1, tab2, tab3 = st.tabs(["Career Flow", "Experience Details", "Education"])
        
        with tab1:
            render_sankey_chart(st.session_state.resume_data)
        
        with tab2:
            render_company_summaries(st.session_state.resume_data)
        
        with tab3:
            render_education(st.session_state.resume_data)
    else:
        st.info("Upload a resume to begin processing")

def render_search_tab():
    """Display search interface"""
    with st.expander("Search Resumes"):
        search_query = st.text_input("Enter search terms...")
        if search_query:
            results = backend.search_resumes(search_query)
            display_search_results(results)

def deploy_kubernetes_worker():
    """Deploy or update resume processor in Kubernetes"""
    try:
        k8s_config.load_kube_config()
        api = k8s_client.AppsV1Api()
        
        container = k8s_client.V1Container(
            name="resume-worker",
            image="ghcr.io/yourorg/resume-processor:latest",
            env=[
                k8s_client.V1EnvVar(name="ELASTIC_HOST", value=config.elastic_host),
                k8s_client.V1EnvVar(name="KAFKA_BROKERS", value=config.kafka_bootstrap_servers),
                k8s_client.V1EnvVar(name="GROK_API_KEY", value=config.grok_api_token)
            ]
        )
        
        deployment = k8s_client.V1Deployment(
            metadata=k8s_client.V1ObjectMeta(name="resume-processor"),
            spec=k8s_client.V1DeploymentSpec(
                replicas=1,
                selector=k8s_client.V1LabelSelector(
                    match_labels={"app": "resume-processor"}
                ),
                template=k8s_client.V1PodTemplateSpec(
                    metadata=k8s_client.V1ObjectMeta(
                        labels={"app": "resume-processor"}
                    ),
                    spec=k8s_client.V1PodSpec(containers=[container])
                )
            )
        )
        
        try:
            # Try to patch (update) the deployment if it exists
            api.patch_namespaced_deployment(
                name="resume-processor",
                namespace="default",
                body=deployment
            )
            st.success("Worker deployment updated (rolling update)!")
        except ApiException as e:
            if e.status == 404:
                # Not found, so create it
                api.create_namespaced_deployment(namespace="default", body=deployment)
                st.success("Worker deployment created!")
            elif e.status == 409:
                st.warning("Deployment already exists. Updating deployment instead.")
                api.patch_namespaced_deployment(
                    name="resume-processor",
                    namespace="default",
                    body=deployment
                )
                st.success("Worker deployment updated!")
            else:
                raise

    except Exception as e:
        st.error(f"Deployment failed: {str(e)}")

def save_uploaded_file(file, user_id):
    """Save uploaded file with proper permissions"""
    upload_dir = os.path.join(config.upload_dir, user_id)
    os.makedirs(upload_dir, exist_ok=True, mode=0o755)
    file_path = os.path.join(upload_dir, file.name)
    
    with open(file_path, "wb") as f:
        f.write(file.getbuffer())
    
    return file_path

def display_search_results(results):
    """Display formatted search results"""
    for hit in results.get('hits', {}).get('hits', []):
        with st.expander(f"Resume {hit['_id']}"):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.metric("Score", f"{hit['_score']:.2f}")
            with col2:
                st.write(f"**Skills:** {', '.join(hit['_source'].get('skills', []))}")
                st.write(f"**Experience:** {hit['_source'].get('experience', '')}")

if __name__ == "__main__":
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'ready_to_deploy' not in st.session_state:
        st.session_state.ready_to_deploy = False
    main_ui()

