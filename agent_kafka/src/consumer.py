import os
import json
import logging
from kafka import KafkaConsumer
from redis import Redis
from redis.cluster import RedisCluster
from agent_core.interfaces.config import AppConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KafkaStreamProcessor:
    def __init__(self, config: AppConfig = None):
        # Get configuration from environment variables or config
        self.kafka_servers = os.getenv(
            'KAFKA_BOOTSTRAP_SERVERS', 
            config.kafka_bootstrap_servers if config else '192.168.2.200:9092'
        )
        self.kafka_group_id = os.getenv(
            'KAFKA_GROUP_ID',
            config.kafka_group_id if config else 'video-views-group'
        )
        
        # Initialize Redis client
        self.redis = self._init_redis(config)
        
        # Create Kafka consumer
        self.consumer = KafkaConsumer(
            os.getenv("KAFKA_TOPIC", "videos-views"),
            bootstrap_servers=self.kafka_servers,
            group_id=self.kafka_group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logger.info(f"Initialized Kafka consumer for {self.kafka_servers}")

    def _init_redis(self, config):
        redis_mode = os.getenv('REDIS_MODE', 'single')
        redis_nodes = os.getenv('REDIS_NODES', '').split(',') or (
            [f"{node.host}:{node.port}" for node in config.redis_nodes] 
            if config else ['127.0.0.1:6379']
        )

        if redis_mode == 'single':
            host, port = redis_nodes[0].split(':')
            logger.info(f"Connecting to Redis at {host}:{port}")
            return Redis(
                host=host,
                port=int(port),
                decode_responses=True
            )
        else:
            logger.info(f"Connecting to Redis cluster at {redis_nodes}")
            return RedisCluster(
                startup_nodes=[{"host": n.split(":")[0], "port": n.split(":")[1]} 
                             for n in redis_nodes],
                decode_responses=True
            )

    def process_stream(self, topic=None):
        """Process messages from Kafka topic."""
        target_topic = topic or os.getenv('KAFKA_TOPIC', 'videos-views')
        self.consumer.subscribe([target_topic])
        logger.info(f"Subscribed to topic: {target_topic}")

        try:
            while True:
                messages = self.consumer.poll(timeout_ms=1000)
                if not messages:
                    logger.debug("No messages received")
                    continue

                for _, records in messages.items():
                    for msg in records:
                        try:
                            self._process_message(msg)
                            self.consumer.commit(asynchronous=False)
                        except Exception as e:
                            logger.error(f"Failed to process message: {str(e)}")
                            continue

                logger.debug("Committed offsets")

        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        except Exception as e:
            logger.error(f"Fatal error: {str(e)}")
        finally:
            self.consumer.close()
            logger.info("Kafka consumer closed")

    def _process_message(self, msg):
        """Process individual message."""
        logger.debug(f"Received message: {msg.value}")
        
        try:
            video_id = msg.value['videoid']
            views = self.redis.hincrby('video_views', video_id, 1)
            logger.info(f"Updated views for {video_id} - Total: {views}")
        except KeyError:
            logger.warning(f"Malformed message missing 'videoid': {msg.value}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

if __name__ == "__main__":
    # For standalone execution
    processor = KafkaStreamProcessor()
    processor.process_stream()

