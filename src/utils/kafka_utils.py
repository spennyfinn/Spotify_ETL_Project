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
        'max.in.flight.requests.per.connection': 1
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
    except json.JSONDecodeError as e:
        print(f"There was an JSON error for track: {track} with error: {e}")
        return
    if topic_name=='music_top_tracks':
        try:
            producer.produce( topic=topic_name, key=track['song_id'], value = track_json)
            print(f"Message queued: {track['name']} through {topic_name}")
        except Exception as e:
            print(f"Failed to send track {track['name']}: {e}")
            return
    elif topic_name=='music_transformed':
        try:
            producer.produce( topic=topic_name, key=track['song_id'], value = track_json)
            print(f"Message queued: {track.get('song_name', 'Unknown')} through {topic_name}")
        except Exception as e:
            print(f"Failed to send track {track.get('song_name', 'Unknown')}: {e}")
            return
    elif topic_name == 'lastfm_artist':
        try:
            producer.produce(topic= topic_name, key=track['artist_name'], value=track_json)
            print(f"Message queued: {track['song_name']} through {topic_name}")
        except Exception as e:
            print(f"Failed to send track {track['song_name']}: {e}")
            return
    elif topic_name == 'music_audio_features':
        try:
            producer.produce(topic=topic_name, key=track['song_id'], value=track_json)
            print(f'Message queued: {track['name']} through {topic_name}')
        except Exception as e:
            print(f'Failed to send track {track['name']}: {e}')
            return
    else:
        print(f'Unknown topic_name: {topic_name}')
        return


def flush_kafka_producer(producer:Producer):
    """Flush all queued messages to Kafka."""
    producer.flush()
