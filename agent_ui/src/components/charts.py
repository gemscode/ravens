# components/charts.py
from streamlit_echarts import st_echarts
from models import ResumeData

def render_sankey_chart(resume_data: ResumeData):
    """Render interactive Sankey diagram using ECharts"""
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

def render_skills_heatmap(skills_data: dict):
    """Render skills proficiency heatmap using ECharts"""
    options = {
        "title": {"text": "Skills Proficiency Matrix", "left": "center"},
        "tooltip": {"position": "top"},
        "xAxis": {"type": "category", "data": list(skills_data.keys())},
        "yAxis": {"type": "category", "data": ["Proficiency"]},
        "visualMap": {
            "min": 0,
            "max": 100,
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "bottom": "0%"
        },
        "series": [{
            "type": "heatmap",
            "data": [[skill, "Proficiency", prof] for skill, prof in skills_data.items()],
            "label": {"show": True},
            "emphasis": {"itemStyle": {"shadowBlur": 10}}
        }]
    }
    st_echarts(options=options, height="400px")

def render_experience_timeline(experience_data: list):
    """Render career timeline using ECharts"""
    options = {
        "title": {"text": "Professional Timeline", "left": "center"},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "time"},
        "yAxis": {"type": "value", "show": False},
        "series": [{
            "type": "line",
            "data": [
                [exp['start_date'], exp['company'], exp['position']]
                for exp in experience_data
            ],
            "symbolSize": 10,
            "markLine": {
                "data": [
                    {"xAxis": exp['start_date'], "name": exp['company']}
                    for exp in experience_data
                ]
            }
        }]
    }
    st_echarts(options=options, height="500px")

