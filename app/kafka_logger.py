import os
import json
from aiokafka import AIOKafkaProducer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "request_logs")

producer: AIOKafkaProducer | None = None

async def start_producer():
    global producer
    if producer is None:
        producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
        await producer.start()

async def stop_producer():
    global producer
    if producer is not None:
        await producer.stop()
        producer = None

async def send_log(message: dict):
    """
    Send a JSON-encoded message to Kafka. Assumes producer was started.
    If the producer is not started, start it lazily.
    """
    global producer
    if producer is None:
        await start_producer()
    # ensure bytes
    await producer.send_and_wait(KAFKA_TOPIC, json.dumps(message).encode("utf-8"))
