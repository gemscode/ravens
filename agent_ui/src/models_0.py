from pydantic import BaseModel
from typing import Dict, List, Optional

class ResumeData(BaseModel):
    companies: List[Dict]
    technology_categories: List[Dict]
    project_technology_links: List[Dict]
    experiences: List[Dict]

class ProcessingEvent(BaseModel):
    file_path: str
    user_id: str
    status: str = "pending"
