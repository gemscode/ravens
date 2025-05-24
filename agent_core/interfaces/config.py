# agent_core/interfaces/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from redis.cluster import ClusterNode
from typing import List, Optional

class AppConfig(BaseSettings):
    redis_host: str = "192.168.2.200"
    redis_port: int = 6379 
    redis_nodes: List[ClusterNode] = [
        ClusterNode(host="127.0.0.1", port=7001),
        ClusterNode(host="127.0.0.1", port=7002),
        ClusterNode(host="127.0.0.1", port=7003)
    ]
    kafka_bootstrap_servers: str = "192.168.2.200:9092"
    kafka_group_id: str = "views-counter"
    
    # Optional fields
    grok_api_token: Optional[str] = None
    redis_cluster_nodes: Optional[str] = None
    elastic_host: Optional[str] = None
    upload_dir: Optional[str] = None
    processor_image: Optional[str] = None

    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"  # Allow extra fields in .env without validation errors
    )

