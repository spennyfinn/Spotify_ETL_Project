import logging
import json
import os
from confluent_kafka import Consumer, Producer



# -------------------------------
# Kafka Config Functions
# -------------------------------
def get_consumer_config(group_id):
    return{
        'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", 'localhost:9092'),
        'group.id': group_id,
        'auto.offset.reset': "earliest",
        'enable.auto.commit': True,
        'auto.commit.interval.ms' : 1000
    }

def get_producer_config(client_id):
    return {
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'client.id': client_id,
        'acks': 'all',
        'retries': 3,
        'max.in.flight.requests.per.connection': 1
    }

def create_consumer(group_id):
    config= get_consumer_config(group_id)
    return Consumer(config)

def create_producer(client_id):
    config = get_producer_config(client_id)
    return Producer(config)



# -------------------------------
# Kafka Functions
# -------------------------------
def consume_message(consumer, topic):
    """
    Continuously poll messages from a Kafka topic and yield them as JSON objects.

    Args:
        consumer (Consumer): Kafka consumer instance
        topic (str): Kafka topic to subscribe to

    Yields:
        dict: Parsed JSON message from Kafka
    """
    consumer.subscribe([topic])
    logging.info(f"Subscribed to topic: {topic}")
    
    while True:
        msg=consumer.poll(1.0)
        if msg == None:
            continue
        if msg.error():
            logging.error(f'Kafka error: {msg.error()}')
            continue
        try:
            encoded_value=msg.value().decode('utf-8')
            yield json.loads(encoded_value)
        except json.JSONDecodeError as e:
            logging.error(f'Failed to parse JSON: {e}')
            try:
                logging.debug(f'Message content: {encoded_value[:200]}...')
            except:
                pass
            continue
        except UnicodeDecodeError as e:
            logging.error(f'Failed to decode value: {e}')
            continue
        except Exception as e:
            logging.error(f'Unexpected error processing message: {e}')
            continue
 
def send_through_kafka(track, topic_name, producer):
    # sends data to kafka
    track_json = json.dumps(track)
    try:
        producer.produce( topic=topic_name, key=track['song_id'], value = track_json)
        try:
            print(f"Message queued: {track['name']}")
        except KeyError:
            print(f"Message queued: {track['song_name']}")
    except Exception as e:
        print(f"Failed to send track {track['name']}: {e}")
        return

def flush_kafka_producer(producer):
    """Flush all queued messages to Kafka."""
    producer.flush()
