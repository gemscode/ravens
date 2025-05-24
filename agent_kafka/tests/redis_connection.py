# test_redis_cluster.py
from redis.cluster import RedisCluster, ClusterNode
from agent_core.interfaces.config import AppConfig
from agent_redis.src.client import RedisClient

startup_nodes = [
    ClusterNode(host="127.0.0.1", port=7001),
    ClusterNode(host="127.0.0.1", port=7002),
    ClusterNode(host="127.0.0.1", port=7003)
]
rc = RedisCluster(startup_nodes=startup_nodes, decode_responses=True)

# Test write/read
rc.set("test_key", "test_value")
print(rc.get("test_key"))  # Should output "test_value"

# Test increment
rc.incr("test_counter")
print(rc.get("test_counter"))  # Should output "1"

