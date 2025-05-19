# app.py
import streamlit as st
import os
from datetime import datetime
from models import ResumeMetadata, ResumeData
from services import BackendService
from helpers import save_uploaded_file, deploy_resume_processor
from streamlit_echarts import st_echarts

def main():
    """Main application entry point"""
    st.set_page_config(page_title="AI Resume Analyzer", layout="wide")
    backend = BackendService()
    
    # Initialize session state
    if 'selected_resume' not in st.session_state:
        st.session_state.selected_resume = None
    
    # Application header
    st.title("📄 AI Resume Analyzer")
    
    # Sidebar components
    with st.sidebar:
        processed_resumes_list(backend)
        handle_file_upload(backend)
        handle_deployment(backend)
    
    # Main content area
    if st.session_state.selected_resume:
        display_resume_analysis(st.session_state.selected_resume)
    else:
        st.info("👈 Select a resume from the sidebar to view analysis")

def transform_groq_to_sankey(groq_analysis):
    """Transform GROQ analysis into ECharts Sankey format"""
    nodes = []
    links = []
    node_names = set()  # Track nodes to avoid duplicates
    
    # Add companies as nodes
    if 'professional_experience' in groq_analysis:
        for exp in groq_analysis['professional_experience']:
            company_name = exp.get('company', '')
            if company_name and company_name not in node_names:
                nodes.append({"name": company_name})
                node_names.add(company_name)
                
            # Create a project node for each company
            project_name = f"{company_name} - Projects"
            if project_name not in node_names:
                nodes.append({"name": project_name})
                node_names.add(project_name)
                
            links.append({
                "source": company_name,
                "target": project_name,
                "value": 1
            })
            
            # Link projects to technologies
            if 'technologies' in exp:
                for tech in exp.get('technologies', []):
                    if tech not in node_names:
                        nodes.append({"name": tech})
                        node_names.add(tech)
                    
                    links.append({
                        "source": project_name,
                        "target": tech,
                        "value": 1
                    })
    
    # Add technology categories
    if 'technical_skills' in groq_analysis:
        for category, techs in groq_analysis['technical_skills'].items():
            category_name = category.title()
            
            if category_name not in node_names:
                nodes.append({"name": category_name})
                node_names.add(category_name)
            
            for tech in techs:
                if tech in node_names:  # only link if tech node exists
                    links.append({
                        "source": tech,
                        "target": category_name,
                        "value": 1
                    })
    
    return {"nodes": nodes, "links": links}

def display_technical_skills(groq_analysis):
    """Display technical skills grouped by category"""
    if 'technical_skills' not in groq_analysis:
        return
    
    cols = st.columns(3)
    
    for i, (category, skills) in enumerate(groq_analysis['technical_skills'].items()):
        with cols[i % 3]:
            st.subheader(category.title())
            for skill in skills:
                st.markdown(f"- {skill}")

def processed_resumes_list(backend: BackendService):
    """Sidebar list of processed resumes with working dropdown selection"""
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
            st.info("No processed resumes found")
            return
        
        # Store resume data for lookup
        resume_dict = {}
        for hit in result['hits']['hits']:
            resume_dict[hit['_source']['filename']] = hit
        
        # Initialize session state for selected resume if not already set
        if 'selected_resume_filename' not in st.session_state:
            st.session_state.selected_resume_filename = list(resume_dict.keys())[0]
            
        # Create selectbox with current value from session state
        selected_filename = st.selectbox(
            "Select Resume",
            options=list(resume_dict.keys()),
            index=list(resume_dict.keys()).index(st.session_state.selected_resume_filename) 
            if st.session_state.selected_resume_filename in resume_dict else 0,
            key="resume_selector"
        )
        
        # Update session state when selection changes
        st.session_state.selected_resume_filename = selected_filename
        
        # Display selected resume info
        selected_resume_source = resume_dict[selected_filename]['_source']
        st.caption(f"Uploaded: {selected_resume_source['upload_date'].split('T')[0]}")
        
        if 'groq_analysis' in selected_resume_source and 'technical_skills' in selected_resume_source['groq_analysis']:
            languages = selected_resume_source['groq_analysis']['technical_skills'].get('languages', [])
            if languages:
                st.write("**Top Skills:**")
                st.write(", ".join(languages[:3]))
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Analyze", key="analyze_btn"):
                st.session_state.selected_resume = resume_dict[selected_filename]
        with col2:
            if st.button("🗑️ Delete", key="delete_btn"):
                try:
                    if backend.delete_resume(resume_dict[selected_filename]['_id']):
                        st.success(f"Deleted {selected_filename}")
                        st.rerun()
                    else:
                        st.error("Failed to delete resume")
                except Exception as e:
                    st.error(f"Error deleting resume: {str(e)}")
                    
    except Exception as e:
        st.error(f"Error loading resumes: {str(e)}")

def processed_resumes_list___(backend: BackendService):
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
            
        # Create a dictionary mapping filenames to hit objects for lookup
        resume_hits = {hit['_source']['filename']: hit for hit in result['hits']['hits']}
        
        # Create the selectbox with filenames
        selected_filename = st.selectbox(
            "Select a Resume",
            options=list(resume_hits.keys()),
            key="resume_selector"
        )
        
        # Display buttons side by side
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Analyze", key="analyze_btn"):
                st.session_state.selected_resume = resume_hits[selected_filename]
        with col2:
            if st.button("🗑️ Delete", key="delete_btn"):
                if backend.delete_resume(resume_hits[selected_filename]['_id']):
                    st.success(f"Deleted {selected_filename}")
                    st.experimental_rerun()
                else:
                    st.error("Failed to delete resume")
        
        # Show details of selected resume
        if selected_filename and selected_filename in resume_hits:
            resume = resume_hits[selected_filename]['_source']
            st.caption(f"Uploaded: {resume['upload_date'].split('T')[0]}")
            if 'groq_analysis' in resume and 'technical_skills' in resume['groq_analysis']:
                languages = resume['groq_analysis']['technical_skills'].get('languages', [])
                if languages:
                    st.write("**Top Skills:**")
                    st.write(", ".join(languages[:3]))
    
    except Exception as e:
        st.error(f"Error loading resumes: {str(e)}")

def handle_file_upload(backend: BackendService):
    """File upload section"""
    with st.expander("📤 Upload New Resume", expanded=True):
        uploaded_file = st.file_uploader("Choose resume file", type=["pdf", "docx"])
        user_id = st.text_input("User ID", help="Unique session identifier")
        
        if uploaded_file and user_id:
            try:
                file_path = save_uploaded_file(
                    file=uploaded_file,
                    user_id=user_id,
                    upload_dir=os.path.join("uploads", user_id)
                )
                checksum = backend.calculate_checksum(file_path)
                
                if backend.check_existing_resume(checksum):
                    st.info("⏳ This resume is already being processed")
                    return
                
                metadata = ResumeMetadata(
                    checksum=checksum,
                    filename=uploaded_file.name,
                    file_path=file_path,
                    user_id=user_id,
                    upload_date=datetime.now()
                )
                backend.create_resume_document(metadata)
                st.success("✅ Resume queued for processing!")
                st.session_state.ready_to_deploy = True
                
            except Exception as e:
                st.error(f"❌ Upload failed: {str(e)}")

def handle_deployment(backend: BackendService):
    """Cluster deployment controls"""
    with st.expander("⚙️ Cluster Management", expanded=True):
        if st.button("🚀 Deploy Processor", 
                    disabled=not st.session_state.get('ready_to_deploy', False)):
            if deploy_resume_processor(st.session_state.get('user_id', 'default')):
                st.success("🎉 Worker deployed successfully!")
            else:
                st.error("❌ Deployment failed - check logs")

def display_resume_analysis(resume):
    """Display analysis for selected resume"""
    doc = resume['_source']
    
    # Header section below visualization
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        st.subheader(doc['filename'])
    with col2:
        st.metric("Status", doc['status'].capitalize())
    with col3:
        st.metric("Upload Date", doc['upload_date'].split('T')[0])
    
    # Tabs for Experience, Technical Skills, and Education
    # Show Sankey diagram FIRST using groq_analysis directly
    if 'groq_analysis' in doc:
        try:
            st.header("Career Flow Visualization")
            
            # Transform data for Sankey chart
            sankey_data = transform_groq_to_sankey(doc['groq_analysis'])
            
            # Configure ECharts options
            options = {
                "tooltip": {"trigger": "item", "triggerOn": "mousemove"},
                "series": [{
                    "type": "sankey",
                    "data": sankey_data["nodes"],
                    "links": sankey_data["links"],
                    "emphasis": {"focus": "adjacency"},
                    "levels": [
                        {"depth": 0, "itemStyle": {"color": "#fbb4ae"}},
                        {"depth": 1, "itemStyle": {"color": "#b3cde3"}},
                        {"depth": 2, "itemStyle": {"color": "#ccebc5"}},
                        {"depth": 3, "itemStyle": {"color": "#decbe4"}}
                    ],
                    "lineStyle": {"curveness": 0.5}
                }]
            }
            
            # Render the Sankey chart
            st_echarts(options=options, height="600px")
            
        except Exception as e:
            st.error(f"Error creating Sankey diagram: {str(e)}")
            st.json(doc['groq_analysis'])
    
    tab1, tab2, tab3 = st.tabs(["Professional Experience", "Technical Skills", "Education"])
    
    with tab1:
        if 'groq_analysis' in doc and 'professional_experience' in doc['groq_analysis']:
            for i, exp in enumerate(doc['groq_analysis']['professional_experience']):
                with st.expander(f"{exp.get('position', '')} at {exp.get('company', '')}", expanded=i==0):
                    st.write(f"**Duration:** {exp.get('duration', '')}")
                    
                    if 'achievements' in exp and exp['achievements']:
                        st.write("**Achievements:**")
                        for achievement in exp['achievements']:
                            st.write(f"- {achievement}")
                    
                    if 'technologies' in exp and exp['technologies']:
                        st.write("**Technologies:**")
                        st.write(", ".join(exp['technologies']))
        else:
            st.warning("No professional experience data available")
    
    with tab2:
        if 'groq_analysis' in doc and 'technical_skills' in doc['groq_analysis']:
            display_technical_skills(doc['groq_analysis'])
        else:
            st.warning("No technical skills data available")
    
    with tab3:
        if 'groq_analysis' in doc and 'education' in doc['groq_analysis']:
            for edu in doc['groq_analysis']['education']:
                with st.expander(f"{edu.get('degree')} at {edu.get('institution')}"):
                    if 'field_of_study' in edu:
                        st.write(f"**Field:** {edu['field_of_study']}")
        else:
            st.warning("No education data available")

# Add delete_resume method to BackendService (needs to be added to services.py)
def delete_resume(backend: BackendService, doc_id: str) -> bool:
    """Delete a resume document from Elasticsearch"""
    try:
        response = backend.es.delete(
            index="resumes",
            id=doc_id,
            refresh=True
        )
        return response.get('result') == 'deleted'
    except Exception as e:
        st.error(f"Failed to delete document {doc_id}: {str(e)}")
        return False
        
# Add this method to your BackendService class in services.py
BackendService.delete_resume = delete_resume

if __name__ == "__main__":
    main()

