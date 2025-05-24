# test_redis.py
from agent_core.interfaces.config import AppConfig
from agent_redis.src.client import RedisClient

config = AppConfig()
redis_client = RedisClient(config)

print("Video 0001 views:", redis_client.client.get("video_views:0001") or 0)
print("Video 0002 views:", redis_client.client.get("video_views:0002") or 0)

