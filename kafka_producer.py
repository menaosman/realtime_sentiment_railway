from kafka import KafkaProducer
import json
import time
import random

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

sample_texts = [
    "I love this product!", "This is the worst movie ever.",
    "It's an average day.", "Absolutely fantastic!", "I hate traffic."
]

while True:
    tweet = {
        "Text": random.choice(sample_texts),
        "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    producer.send('tweets', tweet)
    print("Sent:", tweet)
    time.sleep(3)
