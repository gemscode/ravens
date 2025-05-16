# agent_redis/src/client.py
from redis import Redis, RedisCluster
from agent_core.interfaces.config import AppConfig

class RedisClient:
    def __init__(self, config: AppConfig):
        self.config = config
        self.client = self._initialize_redis()

    def _initialize_redis(self):
        try:
            # For Redis Cluster
            return RedisCluster(
                startup_nodes=self.config.redis_nodes,
                decode_responses=True
            )
        except Exception as e:
            # Fallback to standalone Redis
            node = self.config.redis_nodes[0]
            return Redis(
                host=node["host"],
                port=node["port"],
                decode_responses=True
            )

    def increment_video_view(self, video_id: str):
        self.client.incr(f"video_views:{video_id}")

    def get_video_views(redis_client, topic_name):
        """Get all video view counts for a topic."""
        # Get all keys matching the pattern
        keys = redis_client.client.keys(f"video_views:*")
    
        # Get counts for each key
        counts = {}
        for key in keys:
           video_id = key.split(':')[1]
           count = redis_client.client.get(key)
           counts[video_id] = int(count) if count else 0
    
        return counts

