# agent_ui/src/models.py
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import date, datetime

class CompanyExperience(BaseModel):
    name: str
    position: str
    start_date: date
    end_date: date
    location: str
    description: str
    projects: List['Project'] = []
    technologies: List[str] = []
    
    @property
    def duration(self) -> str:
        months = (self.end_date.year - self.start_date.year) * 12 + \
                (self.end_date.month - self.start_date.month)
        return f"{months//12}y {months%12}m"

class Project(BaseModel):
    name: str
    client: str
    start_date: date
    end_date: date
    description: str
    technologies: List[str] = []
    
    @property
    def duration_months(self) -> int:
        return (self.end_date.year - self.start_date.year) * 12 + \
              (self.end_date.month - self.start_date.month)

class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    start_date: date
    end_date: date
    gpa: Optional[str] = None
    description: Optional[str] = None

class ResumeData(BaseModel):
    """Structured resume content after parsing"""
    companies: List[CompanyExperience] = []
    education: List[Education] = []
    skills: List[str] = []
    certifications: List[str] = []

class ResumeMetadata(BaseModel):
    """Metadata for tracking resume processing"""
    checksum: str  # CRC32 checksum of the file
    filename: str
    upload_date: datetime
    user_id: str
    status: str = "pending"  # pending/processing/processed
    processed_data: Optional[ResumeData] = None

class ProcessingEvent(BaseModel):
    """Event for Kafka queue"""
    file_path: str
    checksum: str  # Matches ResumeMetadata.checksum
    user_id: str
    status: str = "pending"
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }

