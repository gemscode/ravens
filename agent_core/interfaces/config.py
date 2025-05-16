from pydantic_settings import BaseSettings
from redis.cluster import ClusterNode
from typing import List

class AppConfig(BaseSettings):
    # Redis

    redis_nodes: List[ClusterNode] = [
       ClusterNode(host="127.0.0.1", port=7001),
       ClusterNode(host="127.0.0.1", port=7002),
       ClusterNode(host="127.0.0.1", port=7003)
    ]
    
    # Kafka
    kafka_bootstrap_servers: str = "192.168.2.201:9092"
    kafka_group_id: str = "views-counter"
    
    class Config:
        env_file = ".env"

