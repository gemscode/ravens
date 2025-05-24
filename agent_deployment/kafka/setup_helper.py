from kafka import KafkaAdminClient, KafkaProducer
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable
import os
import time
import json

def create_topic():
    topic = os.getenv("SETUP_TOPIC", "videos-views")
    admin = KafkaAdminClient(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        request_timeout_ms=10000
    )
    
    try:
        existing_topics = admin.list_topics()
        if topic in existing_topics:
            print(f"Topic '{topic}' already exists")
            return

        print(f"Creating topic '{topic}'")
        admin.create_topics([NewTopic(topic, num_partitions=3, replication_factor=1)])
    finally:
        admin.close()

def produce_sample_messages():
    producer = KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        acks='all',
        retries=3,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')  # JSON serializer
    )
    
    try:
        print("Producing sample messages...")
        for i in range(10):
            message = {"videoid": f"video_{i}"}  # Correct message format
            producer.send(
                topic=os.getenv("SETUP_TOPIC"),
                key=f"video_{i}".encode(),
                value=message
            )
        producer.flush()
        print("Successfully produced sample messages")
    finally:
        producer.close()

if __name__ == "__main__":
    max_retries = 5
    for attempt in range(max_retries):
        try:
            create_topic()
            produce_sample_messages()
            break
        except (NoBrokersAvailable, ConnectionError) as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed after {max_retries} attempts: {str(e)}")
            print(f"Attempt {attempt+1}/{max_retries}: {str(e)}")
            time.sleep(5)

