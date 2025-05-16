# agent_kafka/run_consumer.py
import logging
from agent_core.interfaces.config import AppConfig
from consumer import KafkaStreamProcessor

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    config = AppConfig()
    processor = KafkaStreamProcessor(config, topic="views_count")
    
    try:
        logging.info("Starting Kafka consumer for topic 'views_count'")
        processor.process_stream()
    except KeyboardInterrupt:
        logging.info("Consumer stopped by user")
    except Exception as e:
        logging.error(f"Consumer failed: {str(e)}")
        raise
