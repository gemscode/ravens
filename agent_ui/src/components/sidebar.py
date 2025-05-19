# components/sidebar.py
import streamlit as st
from datetime import datetime
from services import BackendService
from helpers.file_io import save_uploaded_file
from models import ResumeMetadata

def processed_resumes_list(backend: BackendService):
    """Sidebar list of processed resumes with delete functionality"""
    st.header("📁 Processed Resumes")
    try:
        result = backend.es.search(
            index="resumes",
            body={
                "query": {"match_all": {}},
                "sort": [{"upload_date": {"order": "desc"}}],
                "size": 10
            }
        )
        
        if not result['hits']['hits']:
            st.info("No resumes processed yet")
            return

        selected_resume = st.selectbox(
            "Select Resume",
            options=[hit['_source']['filename'] for hit in result['hits']['hits']],
            format_func=lambda x: x,
            key="resume_selector"
        )

        col1, col2 = st.columns([2, 2])
        with col1:
            if st.button("Analyze Selected"):
                selected_hit = next(hit for hit in result['hits']['hits'] 
                                  if hit['_source']['filename'] == selected_resume)
                st.session_state.selected_resume = selected_hit
        with col2:
            if st.button("🗑️ Delete", type="primary"):
                selected_hit = next(hit for hit in result['hits']['hits'] 
                                  if hit['_source']['filename'] == selected_resume)
                if backend.delete_resume(selected_hit['_id']):
                    st.success("Resume deleted successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to delete resume")

    except Exception as e:
        st.error(f"Error loading resumes: {str(e)}")

def upload_section(backend: BackendService):
    """File upload component"""
    with st.expander("📤 Upload New Resume", expanded=True):
        uploaded_file = st.file_uploader("Choose resume", type=["pdf", "docx"])
        user_id = st.text_input("User ID", help="Unique session identifier")
        
        if uploaded_file and user_id:
            try:
                file_path = save_uploaded_file(uploaded_file, user_id)
                checksum = backend.calculate_checksum(file_path)
                
                if backend.check_existing_resume(checksum):
                    st.info("This resume is already being processed")
                    return
                
                metadata = ResumeMetadata(
                    checksum=checksum,
                    filename=uploaded_file.name,
                    file_path=file_path,
                    user_id=user_id,
                    upload_date=datetime.now()
                )
                backend.create_resume_document(metadata)
                st.success("Resume queued for processing!")
                
            except Exception as e:
                st.error(f"Upload failed: {str(e)}")

