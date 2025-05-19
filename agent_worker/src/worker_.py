# agent_worker/src/worker.py
import json
import logging
from kafka import KafkaConsumer
from elasticsearch import Elasticsearch
from groq import Groq
from models import ResumeMetadata, ResumeData
from agent_core.interfaces.config import AppConfig

config = AppConfig()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeProcessor:
    def __init__(self):
        self.es = Elasticsearch([config.elastic_host])
        self.grok = Groq(api_key=config.grok_api_token)
        self.consumer = KafkaConsumer(
            'resume-processing',
            bootstrap_servers=config.kafka_bootstrap_servers,
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
    
    def process_queue(self):
        """Main processing loop"""
        logger.info("Starting resume processing worker...")
        for message in self.consumer:
            try:
                event = message.value
                self.process_resume(event['checksum'])
            except Exception as e:
                logger.error(f"Processing failed: {str(e)}")
    
    def process_resume(self, checksum: str):
        """Process a single resume"""
        # Get resume from Elasticsearch
        doc = self.es.get(index="resumes", id=checksum)['_source']
        
        # Update status to processing
        self.update_status(checksum, "processing")
        
        try:
            # Process with Grok
            processed_data = self.process_with_grok(doc['file_path'])
            
            # Update Elasticsearch
            self.es.update(
                index="resumes",
                id=checksum,
                body={
                    "doc": {
                        "status": "processed",
                        "processed_data": processed_data
                    }
                }
            )
            logger.info(f"Processed resume: {checksum}")
            
        except Exception as e:
            self.update_status(checksum, "error")
            logger.error(f"Failed to process {checksum}: {str(e)}")
    
    def process_with_grok(self, file_path: str) -> dict:
        """Process resume with Grok API"""
        # Extract text
        text = self.extract_text(file_path)
        
        # Get categories
        prompt = f"""Extract the following from this resume:
        - companies: list of company names with periods
        - projects: list of projects with client names
        - education: educational background
        - technologies: list of technologies used
        Format as JSON."""
        
        response = self.grok.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt + text}],
            temperature=0
        )
        
        return json.loads(response.choices[0].message.content)
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from PDF/DOCX"""
        if file_path.endswith('.pdf'):
            from pdfminer.high_level import extract_text
            return extract_text(file_path)
        elif file_path.endswith('.docx'):
            from docx import Document
            doc = Document(file_path)
            return '\n'.join([para.text for para in doc.paragraphs])
        else:
            raise ValueError("Unsupported file format")
    
    def update_status(self, checksum: str, status: str):
        """Update processing status"""
        self.es.update(
            index="resumes",
            id=checksum,
            body={"doc": {"status": status}}
        )

if __name__ == "__main__":
    processor = ResumeProcessor()
    processor.process_queue()

