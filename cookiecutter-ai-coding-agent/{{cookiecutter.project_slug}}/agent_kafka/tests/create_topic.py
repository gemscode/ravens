# create_topic_and_events.py
from kafka.admin import KafkaAdminClient, NewTopic
from kafka import KafkaProducer
import json
import time

# Kafka config
bootstrap_servers = '192.168.2.201:9092'  # Verify this IP matches your Kafka broker
topic_name = 'views_count'

# Create topic (if not exists)
try:
    admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
    new_topic = NewTopic(name=topic_name, num_partitions=1, replication_factor=1)
    admin_client.create_topics([new_topic])
    print(f"Topic '{topic_name}' created successfully")
except Exception as e:
    print(f"Topic creation skipped (may already exist): {str(e)}")
finally:
    admin_client.close()

# Produce test events
producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

events = [
    {'videoid': '0001'},
    {'videoid': '0001'},
    {'videoid': '0002'},
    {'videoid': '0002'},
    {'videoid': '0002'}
]

for event in events:
    producer.send(topic_name, value=event)
    print(f"Produced event: {event}")
    time.sleep(0.5)  # Simulate real-time stream

producer.flush()
producer.close()

