# components/forms.py
import streamlit as st
from services import BackendService
from models import ResumeData

def handle_file_upload(backend: BackendService):
    """Centralized upload handling"""
    if 'uploaded_file' not in st.session_state:
        return
    
    try:
        file = st.session_state.uploaded_file
        user_id = st.session_state.user_id
        
        file_path = save_uploaded_file(file, user_id)
        checksum = backend.calculate_checksum(file_path)
        
        metadata = ResumeMetadata(
            checksum=checksum,
            filename=file.name,
            file_path=file_path,
            user_id=user_id,
            upload_date=datetime.now()
        )
        
        backend.create_resume_document(metadata)
        st.session_state.processing_event = {
            "file_path": file_path,
            "checksum": checksum,
            "user_id": user_id
        }
        
    except Exception as e:
        st.error(f"Upload processing failed: {str(e)}")

