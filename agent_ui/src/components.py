# agent_ui/src/components.py
from streamlit_echarts import st_echarts
from models import ResumeData, ResumeMetadata
import streamlit as st
from datetime import datetime

def render_processing_status(backend, user_id: str):
    """Show processing status for current user"""
    st.subheader("Processing Status")
    
    query = {
        "query": {
            "term": {
                "user_id.keyword": user_id
            }
        },
        "sort": [{"upload_date": {"order": "desc"}}]
    }
    
    results = backend.es.search(index="resumes", body=query)
    
    for hit in results['hits']['hits']:
        doc = hit['_source']
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{doc['filename']}**")
            with col2:
                status = doc['status'].capitalize()
                color = "#4CAF50" if status == "Processed" else "#FFA500" if status == "Processing" else "#607D8B"
                st.markdown(f"<span style='color:{color};'>●</span> {status}", unsafe_allow_html=True)
            with col3:
                st.write(f"Uploaded: {datetime.fromisoformat(doc['upload_date']).strftime('%Y-%m-%d %H:%M')}")

def render_resume_list(backend, user_id: str):
    """Show list of processed resumes"""
    st.subheader("Your Resumes")
    
    query = {
        "query": {
            "term": {
                "user_id.keyword": user_id
            }
        },
        "sort": [{"upload_date": {"order": "desc"}}]
    }
    
    results = backend.es.search(index="resumes", body=query)
    
    for hit in results['hits']['hits']:
        doc = hit['_source']
        if doc['status'] == 'processed' and doc.get('processed_data'):
            with st.expander(f"{doc['filename']} - {doc['processed_data'].get('title', '')}"):
                render_resume_details(doc['processed_data'])

def render_resume_details(data: ResumeData):
    """Show detailed resume analysis"""
    # Visualization Section
    col1, col2 = st.columns([3, 1])
    with col1:
        render_sankey_chart(data)
    with col2:
        st.metric("Total Experience", data.total_experience)
        st.metric("Key Skills", len(data.skills))
    
    # Detailed Sections
    render_company_summaries(data)
    render_education(data)
    render_skills(data)

def render_skills(data: ResumeData):
    """Display skills matrix"""
    if data.skills:
        st.subheader("Skills Matrix")
        cols = st.columns(4)
        for idx, skill in enumerate(data.skills):
            cols[idx % 4].success(f"✓ {skill}")

def render_sankey_chart(resume_data: ResumeData):
    """Render interactive Sankey diagram"""
    nodes, links = _build_sankey_data(resume_data)
    
    options = {
        "title": {"text": "Career Technology Flow", "left": "center"},
        "tooltip": {"trigger": "item", "triggerOn": "mousemove"},
        "series": [{
            "type": "sankey",
            "data": nodes,
            "links": links,
            "emphasis": {"focus": "adjacency"},
            "levels": [
                {"depth": 0, "itemStyle": {"color": "#5470c6"}},
                {"depth": 1, "itemStyle": {"color": "#91cc75"}},
                {"depth": 2, "itemStyle": {"color": "#fac858"}},
                {"depth": 3, "itemStyle": {"color": "#ee6666"}}
            ],
            "lineStyle": {"curveness": 0.5}
        }]
    }
    
    st_echarts(options=options, height="600px", key="sankey_chart")

def _build_sankey_data(data: ResumeData):
    """Transform resume data into Sankey nodes/links"""
    nodes = []
    links = []
    node_map = {}

    # Add companies
    for idx, company in enumerate(data.companies):
        node_id = f"company_{idx}"
        nodes.append({"name": company.name, "id": node_id})
        node_map[company.name] = node_id

    # Add projects
    for company in data.companies:
        for project in company.projects:
            project_id = f"project_{project.name}"
            nodes.append({"name": project.name, "id": project_id})
            links.append({
                "source": node_map[company.name],
                "target": project_id,
                "value": project.duration_months
            })
            
            # Link technologies to projects
            for tech in project.technologies:
                tech_id = f"tech_{tech}"
                if tech_id not in node_map:
                    nodes.append({"name": tech, "id": tech_id})
                    node_map[tech] = tech_id
                links.append({
                    "source": project_id,
                    "target": tech_id,
                    "value": 1
                })

    return nodes, links

def render_company_summaries(data: ResumeData):
    """Display company timelines with projects and tech"""
    st.subheader("Professional Experience")
    for company in data.companies:
        with st.expander(f"{company.name} ({company.start_date} - {company.end_date})", expanded=True):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(f"**Role:** {company.position}")
                st.markdown(f"**Duration:** {company.duration}")
                st.markdown(f"**Location:** {company.location}")
            with col2:
                st.markdown(company.description)
                
                st.subheader("Key Projects", divider="gray")
                for project in company.projects:
                    with st.expander(project.name):
                        st.markdown(f"**Client:** {project.client}")
                        st.markdown(f"**Technologies:** {', '.join(project.technologies)}")
                        st.markdown(project.description)

def render_education(data: ResumeData):
    """Display education section"""
    if data.education:
        st.subheader("Education")
        for edu in data.education:
            with st.expander(f"{edu.degree} at {edu.institution}"):
                st.markdown(f"**Dates:** {edu.start_date} - {edu.end_date}")
                st.markdown(f"**Field:** {edu.field_of_study}")
                if edu.gpa:
                    st.markdown(f"**GPA:** {edu.gpa}")
                if edu.description:
                    st.markdown(edu.description)
