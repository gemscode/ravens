from kafka import KafkaConsumer
import json
import logging
from agent_core.interfaces.config import AppConfig
from agent_redis.src.client import RedisClient

class KafkaStreamProcessor:
    def __init__(self, config: AppConfig, topic):
        self.config = config
        self.redis = RedisClient(config)
        self.consumer = KafkaConsumer(
            bootstrap_servers=self.config.kafka_bootstrap_servers,
            group_id=self.config.kafka_group_id,
            auto_offset_reset='earliest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        self.topic = topic
        
    def process_stream(self):
        """Process messages from Kafka topic."""
        self.consumer.subscribe([self.topic])
        
        try:
            while True:
                messages = self.consumer.poll(timeout_ms=500)
                for _, records in messages.items():
                    if not records:
                        continue
                        
                    for msg in records:
                        try:
                            video_id = msg.value['videoid']
                            self.redis.increment_video_view(video_id)
                        except KeyError:
                            logging.warning(f"Malformed message: {msg.value}")
                        except Exception as e:
                            logging.error(f"Error processing message: {str(e)}")
                            
                self.consumer.commit()
                
        except KeyboardInterrupt:
            logging.info("Shutting down Kafka consumer...")
        finally:
            self.consumer.close()

