# In resume_consumer.py
from kafka import KafkaConsumer
from resume_processor import ResumeProcessor

consumer = KafkaConsumer(
    'resume-processing',
    bootstrap_servers=os.getenv("KAFKA_BROKERS"),
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

processor = ResumeProcessor()

for message in consumer:
    try:
        result = processor.process_resume(message.value['file_path'])
        # Store processing result in Redis
        redis_client.set(f"resume:{result['id']}", json.dumps(result))
    except Exception as e:
        log_error(e)

