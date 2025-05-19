# agent_ui/src/services.py
import zlib
import json
import logging
import os
from datetime import datetime
from typing import Optional
from pdfminer.high_level import extract_text as extract_pdf_text
from docx import Document
from kafka import KafkaProducer
from elasticsearch import Elasticsearch
from kubernetes import client as k8s_client, config as k8s_config
from agent_core.interfaces.config import AppConfig

config = AppConfig()
logger = logging.getLogger(__name__)

class BackendService:
    def __init__(self):
        # Elasticsearch client configuration
        self.es = Elasticsearch(
            [config.elastic_host],
            verify_certs=False,
            request_timeout=30
        )
        
        # Kafka producer setup
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=config.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all'
        )

        # Kubernetes client initialization
        try:
            k8s_config.load_kube_config()
            self.k8s_api = k8s_client.AppsV1Api()
        except Exception as e:
            logger.error(f"Kubernetes config error: {str(e)}")
            self.k8s_api = None

    def calculate_checksum(self, file_path: str) -> str:
        """Calculate CRC32 checksum for file content"""
        buf_size = 65536  # 64KB chunks
        crc = 0
        try:
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(buf_size)
                    if not data:
                        break
                    crc = zlib.crc32(data, crc)
            return format(crc & 0xFFFFFFFF, '08x')
        except Exception as e:
            logger.error(f"Checksum calculation failed: {str(e)}")
            raise

    def _extract_text(self, file_path: str) -> str:
        """Extract text from supported file types"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            if file_path.endswith('.pdf'):
                return extract_pdf_text(file_path)
            elif file_path.endswith('.docx'):
                doc = Document(file_path)
                return '\n'.join([p.text for p in doc.paragraphs])
            else:
                raise ValueError(f"Unsupported file type: {file_path}")
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            raise

    def get_resume_document(self, checksum: str) -> Optional[dict]:
        """Retrieve full resume document from Elasticsearch"""
        try:
            response = self.es.get(
                index="resumes",
                id=checksum,
                _source=True,
                ignore=[404]  # Don't throw error if not found
            )
            return response.body if response else None
        except Exception as e:
            logger.error(f"Document retrieval failed: {str(e)}")
            return None

    def create_resume_document(self, metadata) -> dict:
        """Create and index resume document with extracted text"""
        try:
            # Extract text immediately during document creation
            raw_text = self._extract_text(metadata.file_path)
            
            doc_body = {
                **metadata.dict(),
                "status": "text_extracted",
                "raw_text": raw_text,
                "retries": 0,
                "processing_state": {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            self.es.index(
                index="resumes",
                id=metadata.checksum,
                body=doc_body,
                refresh=True
            )

            self.send_processing_event({
               "file_path": metadata.file_path,
               "checksum": metadata.checksum,
               "user_id": metadata.user_id
            })

            return doc_body
        except Exception as e:
            logger.error(f"Document creation failed: {str(e)}")
            raise

    def send_processing_event(self, event: dict):
        """Send event to Kafka queue"""
        try:
            future = self.kafka_producer.send(
                'resume-processing',
                value=event
            )
            future.add_errback(
                lambda e: logger.error(f"Kafka send failed: {str(e)}")
            )
            self.kafka_producer.flush()
        except Exception as e:
            logger.error(f"Event sending failed: {str(e)}")
            raise

    def check_existing_resume(self, checksum: str) -> bool:
        """Check if resume exists in Elasticsearch"""
        try:
            return self.es.exists(index="resumes", id=checksum)
        except Exception as e:
            logger.error(f"ES existence check failed: {str(e)}")
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
                request_timeout=30
            )
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return {"hits": {"hits": []}}

    # Add this method to the BackendService class
    def delete_resume(self, doc_id: str) -> bool:
        """Delete a resume document from Elasticsearch"""
        try:
            response = self.es.delete(
                index="resumes",
                id=doc_id,
                refresh=True
            )
            return response.get('result') == 'deleted'
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {str(e)}")
            return False

    def deploy_processor(self, user_id: str):
        """Deploy Kubernetes processor pod"""
        if not self.k8s_api:
            logger.error("Kubernetes API not initialized")
            return

        try:
            deployment = k8s_client.V1Deployment(
                metadata=k8s_client.V1ObjectMeta(name=f"resume-processor-{user_id}"),
                spec=k8s_client.V1DeploymentSpec(
                    replicas=1,
                    selector=k8s_client.V1LabelSelector(
                        match_labels={"app": "resume-processor"}
                    ),
                    template=k8s_client.V1PodTemplateSpec(
                        metadata=k8s_client.V1ObjectMeta(
                            labels={"app": "resume-processor"}
                        ),
                        spec=k8s_client.V1PodSpec(
                            containers=[
                                k8s_client.V1Container(
                                    name="processor",
                                    image=config.processor_image,
                                    env=[
                                        k8s_client.V1EnvVar(
                                            name="USER_ID",
                                            value=user_id
                                        )
                                    ]
                                )
                            ]
                        )
                    )
                )
            )
            self.k8s_api.create_namespaced_deployment(
                namespace="default",
                body=deployment
            )
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            raise

