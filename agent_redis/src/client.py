# agent_redis/src/client.py
from redis.cluster import RedisCluster
from redis import Redis
from typing import Optional, Dict

class RedisClient:
    def __init__(self, config, use_local: bool = False):
        if use_local:
            self.client = Redis(
                host=config.redis_host,
                port=config.redis_port,
                decode_responses=True
            )
            print(f"🔍 Debug: Connecting to Redis at {config.redis_host}:{config.redis_port}")
        else:
            self.client = RedisCluster(
                startup_nodes=config.redis_nodes,
                decode_responses=True
            )
        
        # Test connection immediately
        try:
            result = self.client.ping()
            print(f"✅ Redis connection successful: {result}")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            raise

    def get_video_views(self, topic: str = None) -> Dict[str, int]:
        """Get all video views from Redis hash"""
        try:
            print(f"🔍 Debug: Querying Redis for key 'video_views'")
            raw_result = self.client.hgetall("video_views")
            print(f"🔍 Debug: Raw Redis result: {raw_result}")
            print(f"🔍 Debug: Result type: {type(raw_result)}")
            
            if raw_result:
                # Convert to int values if they're strings
                result = {k: int(v) for k, v in raw_result.items()}
                print(f"✅ Processed result: {result}")
                return result
            else:
                print("⚠️ No data found in Redis")
                return {}
        except Exception as e:
            print(f"❌ Redis error: {str(e)}")
            return {}

