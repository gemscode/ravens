# agent_worker/src/worker.py
import json
import logging
from datetime import datetime
from typing import Dict, Any
from kafka import KafkaConsumer, KafkaProducer, TopicPartition
from elasticsearch import Elasticsearch
from agent_core.interfaces.config import AppConfig
from agent_groq.src.groq_processor import GroqProcessor

config = AppConfig()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Queue configurations
MAIN_QUEUE = 'resume-processing'
EXTRACTION_QUEUE = 'resume-extraction-needed'
DLQ_QUEUE = 'resume-processing-dlq'

class ResumeProcessor:
    def __init__(self):
        self.es = Elasticsearch(
            [config.elastic_host],
            verify_certs=False,
            request_timeout=30
        )
        self.groq_processor = GroqProcessor()
        
        # Kafka consumer setup
        self.consumer = KafkaConsumer(
            bootstrap_servers=config.kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            group_id='resume-processor-group'
        )
        
        # Manually assign partition for stability
        topic_partition = TopicPartition(MAIN_QUEUE, 0)
        self.consumer.assign([topic_partition])
        self.consumer.seek_to_beginning()

        # Kafka producer setup
        self.producer = KafkaProducer(
            bootstrap_servers=config.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def process_queue(self):
        """Main processing loop"""
        logger.info("Starting resume processor...")
        try:
            while True:
                records = self.consumer.poll(timeout_ms=1000)
                if not records:
                    continue

                for tp, messages in records.items():
                    for message in messages:
                        try:
                            self._process_message(message)
                        except Exception as e:
                            logger.error(f"Failed to process message: {str(e)}")
                        finally:
                            self.consumer.commit()
        
        except KeyboardInterrupt:
            logger.info("Shutting down processor...")
        finally:
            self.consumer.close()
            self.producer.close()

    def _process_message(self, message):
        """Process individual Kafka message"""
        event = message.value
        checksum = event.get('checksum')
        logger.info(f"Processing checksum: {checksum}")

        # Document existence check
        doc = self.es.get(index="resumes", id=checksum, ignore=[404])
        if not doc.get('found'):
            self._handle_missing_document(event)
            return

        # State validation
        status = doc['_source'].get('status')
        raw_text = doc['_source'].get('raw_text')
        
        if status != "text_extracted" or not raw_text:
            self._handle_text_extraction_needed(event)
            return

        # GROQ processing
        self._process_with_groq(checksum, raw_text, event)

    def _handle_missing_document(self, event):
        """Handle documents not found in Elasticsearch"""
        logger.warning(f"Document not found: {event.get('checksum')}")
        self._send_to_dlq(event, "Document not found in Elasticsearch")

    def _handle_text_extraction_needed(self, event):
        """Route to text extraction queue"""
        logger.info(f"Redirecting to extraction queue: {event.get('checksum')}")
        self.producer.send(EXTRACTION_QUEUE, value=event)
        self.producer.flush()

    def _process_with_groq(self, checksum, raw_text, event):
        """Execute GROQ analysis pipeline"""
        logger.info(f"Starting GROQ analysis for {checksum}")
        try:
            analysis = self.groq_processor.analyze_resume(raw_text)
            self._update_successful_processing(checksum, analysis)
            logger.info(f"Successfully processed {checksum}")
        except Exception as e:
            self._handle_processing_failure(checksum, event, e)

    def _update_successful_processing(self, checksum, analysis):
        """Update ES with successful processing results"""
        update_body = {
            "doc": {
                "status": "processed",
                "groq_analysis": analysis,
                "processed_data": self._transform_analysis(analysis),
                "updated_at": datetime.utcnow().isoformat()
            }
        }
        self.es.update(
            index="resumes",
            id=checksum,
            body=update_body,
            refresh=True
        )

    def _handle_processing_failure(self, checksum, event, error):
        """Handle GROQ processing failures"""
        logger.error(f"GROQ analysis failed for {checksum}: {str(error)}")
        self._update_failed_processing(checksum, str(error))
        self._send_to_dlq(event, f"GROQ processing failed: {str(error)}")

    def _update_failed_processing(self, checksum, error_msg):
        """Mark document as failed in ES"""
        update_body = {
            "doc": {
                "status": "failed_groq",
                "error": error_msg,
                "updated_at": datetime.utcnow().isoformat()
            }
        }
        self.es.update(
            index="resumes",
            id=checksum,
            body=update_body,
            refresh=True
        )

    def _send_to_dlq(self, event, reason):
        """Send failed messages to Dead Letter Queue"""
        dlq_event = {
            **event,
            "error": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.producer.send(DLQ_QUEUE, value=dlq_event)
        self.producer.flush()
        logger.info(f"Sent to DLQ: {event.get('checksum')} - {reason}")

    def _transform_analysis(self, analysis: dict) -> dict:
        """Transform GROQ analysis to standardized format"""
        try:
            return {
                "skills": analysis.get('technical_skills', {}).get('languages', []) +
                         analysis.get('technical_skills', {}).get('frameworks', []),
                "experience": [
                    f"{exp['position']} at {exp['company']}"
                    for exp in analysis.get('professional_experience', [])
                ],
                "education": [
                    {
                        "degree": edu.get('degree', "Unknown Degree"),
                        "institution": edu.get('institution', "Unknown Institution"),
                        "field_of_study": edu.get('field_of_study', "")
                    }
                    for edu in analysis.get('education', [])
                ]
            }
        except Exception as e:
            logger.error(f"Analysis transformation error: {str(e)}")
            return {"error": f"Transformation failed: {str(e)}"}

if __name__ == "__main__":
    processor = ResumeProcessor()
    processor.process_queue()

