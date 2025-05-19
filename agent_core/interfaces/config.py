# agent_core/interfaces/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from redis.cluster import ClusterNode
from typing import List

class AppConfig(BaseSettings):
    # Redis Cluster Configuration
    redis_cluster_nodes: str = Field(
        default="127.0.0.1:7001,127.0.0.1:7002,127.0.0.1:7003", 
        env="REDIS_CLUSTER_NODES",
        description="Comma-separated list of Redis cluster nodes (host:port)"
    )
    
    # Kafka Configuration
    kafka_bootstrap_servers: str = Field(
        default="192.168.2.201:9092", 
        env="KAFKA_BOOTSTRAP_SERVERS",
        description="Kafka broker connection string"
    )
    kafka_group_id: str = Field(
        default="resume-processor-group", 
        env="KAFKA_GROUP_ID",
        description="Consumer group ID for Kafka"
    )
    dlq_topic: str = Field(
        default="resume-processing-dlq", 
        env="DLQ_TOPIC",
        description="Dead Letter Queue topic for failed messages"
    )
    
    # Elasticsearch Configuration
    elastic_host: str = Field(
        default="http://192.168.2.200:9200", 
        env="ELASTIC_HOST",
        description="Elasticsearch connection URL"
    )
    
    # File Handling
    upload_dir: str = Field(
        default="./uploads", 
        env="UPLOAD_DIR",
        description="Directory for storing uploaded files"
    )
    
    # Kubernetes Configuration
    processor_image: str = Field(
        default="ghcr.io/yourorg/resume-processor:latest", 
        env="PROCESSOR_IMAGE",
        description="Docker image for resume processor"
    )
    
    # Grok API Configuration
    grok_api_token: str = Field(
        default="", 
        env="GROK_API_TOKEN",
        description="API token for Grok service"
    )
    grok_model: str = Field(
        default="llama-3.1-70b-versatile", 
        env="GROK_MODEL",
        description="Grok model to use for processing"
    )
    grok_temperature: float = Field(
        default=0.1, 
        env="GROK_TEMPERATURE",
        description="Temperature parameter for LLM generation (0-2)"
    )
    grok_prompt: str = Field(
        default="Extract resume data in JSON format:", 
        env="GROK_PROMPT",
        description="Base prompt for resume parsing"
    )
    
    # Resilience Configuration
    max_retries: int = Field(
        default=3, 
        env="MAX_RETRIES",
        description="Maximum number of processing retries"
    )
    circuit_breaker_timeout: int = Field(
        default=60, 
        env="CIRCUIT_BREAKER_TIMEOUT",
        description="Seconds to wait when circuit is open"
    )
    retry_delay: int = Field(
        default=2, 
        env="RETRY_DELAY",
        description="Seconds between retry attempts"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def redis_nodes(self) -> List[ClusterNode]:
        """Parse Redis cluster nodes into ClusterNode objects"""
        nodes = []
        for node in self.redis_cluster_nodes.split(","):
            host, port = node.strip().split(":")
            nodes.append(ClusterNode(host=host, port=int(port)))
        return nodes

    @field_validator("grok_temperature")
    def validate_temperature(cls, v):
        """Ensure temperature is within valid range"""
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v

