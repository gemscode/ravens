from kafka import KafkaProducer
from elasticsearch import Elasticsearch
from agent_core.interfaces.config import AppConfig
import json
import logging

config = AppConfig()
logger = logging.getLogger(__name__)

class BackendService:
    def __init__(self):
        # Initialize Elasticsearch client
        try:
           self.es = Elasticsearch(
               [config.elastic_host],
               verify_certs=False,
               request_timeout=30 
           )
           # Test connection immediately and print result
           ping_result = self.es.ping()
           print(f"Elasticsearch connection test: {ping_result}")
        except Exception as e:
           logger.error(f"ES Init Error: {str(e)}")
           print(f"Elasticsearch connection failed: {str(e)}")
           # Still initialize to avoid NoneType errors
           self.es = Elasticsearch(
               [config.elastic_host],
               verify_certs=False
           )
        
        # Initialize Kafka producer
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=config.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all'
        )

    def check_elasticsearch(self):
        """Check if Elasticsearch is responsive"""
        try:
            return self.es.ping()
        except Exception as e:
            logger.error(f"ES ping failed: {str(e)}")
            return False

    def search_resumes(self, query: str):
        """Search resumes with enhanced error handling"""
        try:
            return self.es.search(
                index="resumes",
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["skills", "experience", "education"],
                            "fuzziness": "AUTO"
                        }
                    }
                },
                request_timeout=30  # Extended timeout
            )
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return {"hits": {"hits": []}}

    def send_processing_event(self, event):
        """Send event to Kafka with delivery reports"""
        try:
            # Convert event to dict if it has dict method
            value = event.dict() if hasattr(event, "dict") else event
            
            # Send to Kafka and get future
            future = self.kafka_producer.send(
                'resume-processing',
                value=value
            )
            
            # Add success callback
            future.add_callback(
                lambda metadata: logger.info(f"Sent to Kafka: topic={metadata.topic}, partition={metadata.partition}")
            )
            
            # Add error callback
            future.add_errback(
                lambda e: logger.error(f"Failed to send event: {str(e)}")
            )
            
            return True
        except Exception as e:
            logger.error(f"Error sending to Kafka: {str(e)}")
            return False

