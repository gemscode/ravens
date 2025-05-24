from kafka import KafkaAdminClient, KafkaConsumer
from kafka.errors import KafkaError, NoBrokersAvailable
import sys

KAFKA_BOOTSTRAP_SERVERS = "127.0.0.1:9092"
TOPIC_TO_CHECK = "videos-views"

# Test admin connection and list topics
try:
    admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, request_timeout_ms=10000)
    print(f"Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
    topics = admin.list_topics()
    print("Available topics:", topics)
    if TOPIC_TO_CHECK in topics:
        print(f"Topic '{TOPIC_TO_CHECK}' exists.")
    else:
        print(f"Topic '{TOPIC_TO_CHECK}' does NOT exist.")
    admin.close()
except NoBrokersAvailable:
    print("No Kafka brokers available at", KAFKA_BOOTSTRAP_SERVERS)
    sys.exit(1)
except KafkaError as e:
    print("Kafka error:", e)
    sys.exit(1)

# Test consumer connection
try:
    consumer = KafkaConsumer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, consumer_timeout_ms=2000)
    print("KafkaConsumer connection successful.")
    consumer.close()
except Exception as e:
    print("KafkaConsumer connection failed:", e)
    sys.exit(1)

