from streamlit_echarts import st_echarts
from models import ResumeData

def render_sankey_chart(resume_data: ResumeData):
    nodes, links = build_sankey_data(resume_data)
    options = {
        "title": {"text": "Technology Stack Flow"},
        "tooltip": {"trigger": "item"},
        "series": [{
            "type": "sankey",
            "data": nodes,
            "links": links,
            "emphasis": {"focus": "adjacency"},
            "nodeAlign": "left",
            "levels": [
                {"depth": 0, "itemStyle": {"color": "#fbb4ae"}},
                {"depth": 1, "itemStyle": {"color": "#b3cde3"}},
                {"depth": 2, "itemStyle": {"color": "#ccebc5"}},
                {"depth": 3, "itemStyle": {"color": "#decbe4"}}
            ]
        }]
    }
    st_echarts(options=options, height="800px")

def build_sankey_data(resume_data: ResumeData):
    nodes = []
    links = []
    
    # Company nodes
    for company in resume_data.companies:
        nodes.append({"name": company["name"]})
        
    # Project nodes and links
    for proj_link in resume_data.project_technology_links:
        for project in proj_link["projects"]:
            project_name = f"{proj_link['company']} - {project['name']}"
            nodes.append({"name": project_name})
            links.append({
                "source": proj_link["company"],
                "target": project_name,
                "value": 1
            })
    
    # Technology nodes and links
    tech_nodes = set()
    for category in resume_data.technology_categories:
        for tech in category["technologies"]:
            if tech not in tech_nodes:
                nodes.append({"name": tech})
                tech_nodes.add(tech)
    
    # Category nodes and links
    for category in resume_data.technology_categories:
        nodes.append({"name": category["categoryName"]})
        for tech in category["technologies"]:
            links.append({
                "source": tech,
                "target": category["categoryName"],
                "value": 1
            })
    
    return nodes, links
