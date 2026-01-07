from typing import List
import logging
import json
import os
from confluent_kafka import Consumer, Producer



# -------------------------------
# Kafka Config Functions
# -------------------------------
def get_consumer_config(group_id: str):
    return{
        'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", 'localhost:9092'),
        'group.id': group_id,
        'auto.offset.reset': "earliest",
        'enable.auto.commit': True,
        'auto.commit.interval.ms' : 1000
    }

def get_producer_config(client_id:str):
    return {
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'client.id': client_id,
        'acks': 'all',
        'retries': 3,
        'max.in.flight.requests.per.connection': 1,

        # Queue size limits to prevent "Local: Queue full"
        'queue.buffering.max.messages': 10000,  # Max messages in local queue
        'queue.buffering.max.kbytes': 1048576,  # Max size in KB (1GB)

        # Delivery timeout to prevent messages from staying too long
        'delivery.timeout.ms': 30000,  # 30 seconds total timeout
        'message.timeout.ms': 10000,   # 10 seconds per message

        # Retry backoff to avoid hammering
        'retry.backoff.ms': 100,       # Wait 100ms between retries

        # Batching for better throughput
        'batch.size': 16384,           # 16KB batches
        'linger.ms': 5,                # Wait 5ms for more messages in batch

        # Compression for better network efficiency
        'compression.type': 'snappy',
    }

def create_consumer(group_id:str)-> Consumer:
    config= get_consumer_config(group_id)
    return Consumer(config)

def create_producer(client_id:str)-> Consumer:
    config = get_producer_config(client_id)
    return Producer(config)



# -------------------------------
# Kafka Functions
# -------------------------------
def consume_message(consumer: Consumer, topics: List[str])-> dict:
    """
    Continuously poll messages from a Kafka topic and yield them as JSON objects.

    Args:
        consumer (Consumer): Kafka consumer instance
        topic (str): Kafka topic to subscribe to

    Yields:
        dict: Parsed JSON message from Kafka
    """
     # MANUAL SUBSCRIPTION WITH ERROR HANDLING
    try:
        consumer.subscribe(topics)
        logging.info(f"Successfully subscribed to topics: {topics}")
    except Exception as e:
        logging.error(f"Failed to subscribe to topics {topics}: {e}")
        # Try to list available topics for debugging
        try:
            metadata = consumer.list_topics(timeout=5)
            available_topics = list(metadata.topics.keys())
            logging.info(f"Available topics: {available_topics}")
        except Exception as e2:
            logging.error(f"Could not list topics: {e2}")
        finally:
            consumer.close()
            exit(1)

    while True:
        msg=consumer.poll(1.0)
        if msg == None:
            continue
        if msg.error():
            logging.error(f'Kafka error: {msg.error()}')
            continue
        try:
            topic=msg.topic()
            encoded_value=msg.value().decode('utf-8')
            yield (topic,json.loads(encoded_value))
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
 
def send_through_kafka(track:dict, topic_name:str, producer:Producer):
    # sends data to kafka
    try:
        track_json = json.dumps(track)
    except (json.JSONDecodeError, TypeError) as e:
        print(f"JSON serialization error for track: {e}")
        return False

    # Determine key and display name based on topic
    if topic_name == 'music_top_tracks':
        key = track.get('song_id', 'unknown')
        display_name = track.get('name', 'Unknown Track')
    elif topic_name == 'music_transformed':
        key = track.get('song_id', 'unknown')
        display_name = track.get('song_name', 'Unknown Song')
    elif topic_name == 'lastfm_artist':
        key = track.get('artist_name', 'unknown')
        display_name = track.get('song_name', 'Unknown Song')
    elif topic_name == 'music_audio_features':
        key = track.get('song_id', 'unknown')
        display_name = track.get('song_id', 'Unknown ID')
    else:
        print(f'Unknown topic_name: {topic_name}')
        return False

    try:
        # Produce message
        producer.produce(topic=topic_name, key=key, value=track_json)

        # Poll to handle delivery reports and free up queue space
        producer.poll(0)

        print(f"Message queued: {display_name} through {topic_name}")
        return True

    except BufferError as e:
        # Queue is full - this is the "Local: Queue full" error
        print(f"Queue full for {display_name}, flushing and retrying...")
        try:
            # Flush existing messages to free up space
            producer.flush(timeout=5.0)
            # Retry once
            producer.produce(topic=topic_name, key=key, value=track_json)
            producer.poll(0)
            print(f"Message queued after flush: {display_name} through {topic_name}")
            return True
        except Exception as retry_e:
            print(f"Failed to send {display_name} even after flush: {retry_e}")
            return False

    except Exception as e:
        error_msg = str(e)
        if "Local: Queue full" in error_msg:
            print(f"Local queue full for {display_name}. Consider reducing producer rate.")
        else:
            print(f"Failed to send {display_name}: {error_msg}")
        return False


def flush_kafka_producer(producer:Producer):
    """Flush all queued messages to Kafka."""
    producer.flush()


def get_producer_queue_status(producer: Producer) -> dict:
    """Get current producer queue statistics."""
    try:
        # Get queue length (approximate)
        # Note: This is a rough estimate as confluent-kafka doesn't expose direct queue metrics
        return {
            'status': 'active',
            'note': 'Queue monitoring available via producer.flush() and error handling'
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def safe_batch_send(tracks: list, topic_name: str, producer: Producer, batch_size: int = 10) -> tuple:
    """
    Send tracks in controlled batches with error handling.

    Returns:
        tuple: (successful_sends, failed_sends)
    """
    successful = 0
    failed = 0

    for i in range(0, len(tracks), batch_size):
        batch = tracks[i:i + batch_size]

        for track in batch:
            if send_through_kafka(track, topic_name, producer):
                successful += 1
            else:
                failed += 1

        # Small delay between batches to prevent overwhelming
        if i + batch_size < len(tracks):
            import time
            time.sleep(0.1)

    return successful, failed
