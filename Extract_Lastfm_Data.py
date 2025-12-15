"""
Kafka Producer for Last.fm Top Tracks

This script fetches top tracks from Last.fm API, enriches them with track and artist info,
transforms the data, and sends it to a Kafka topic ('music_top_tracks') for downstream processing.

Tech Stack:
- Python, requests, confluent_kafka, uuid
- Last.fm API
- Logging and dotenv for configs
"""

import requests
import json
from confluent_kafka import Producer
import logging
from dotenv import load_dotenv
import os
import math
import uuid
import json
import time

# -------------------------------
# Load Environment Variables
# -------------------------------
load_dotenv()
key=os.getenv("LAST_FM_KEY")


# -------------------------------
# Logging Configuration
# -------------------------------
logging.basicConfig(level=logging.INFO, format="%(message)s")

# -------------------------------
# Kafka Configuration
# -------------------------------
producer_config = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'music-streaming-producer'
}
producer = Producer(producer_config)

# -------------------------------
# Utility Functions
# -------------------------------

def get_artist_id(artist_name, artist_id, artist_id_dict, id_dict_path):
     """
    Retrieve or generate a unique ID for an artist.

    Args:
        artist_name (str): Name of the artist.
        artist_id (str): Existing artist ID, if available.
        artist_id_dict (dict): Dictionary mapping artist names to unique IDs.
        id_dict_path (str): Path to JSON file storing artist IDs.

    Returns:
        str: Unique artist ID (existing or newly generated UUID).
    """
     print(artist_name)
     key =artist_name.strip().lower()
     if artist_id and artist_id!='N/A':
          return artist_id
     if key in artist_id_dict:
          return artist_id_dict[key]
     new_id = str(uuid.uuid4())
     artist_id_dict[key]=new_id
     with open(id_dict_path, 'w') as f:
          json.dump(artist_id_dict, f,indent=4)
     return new_id

def read_id_json_file(artist_id_filepath='artists_ids.json'):
     """Load or initialize JSON file containing artist IDs."""
     if os.path.exists(artist_id_filepath):
         with open(artist_id_filepath,'r') as f:
              artist_id_dict = json.load(f)
              return artist_id_dict
     else:
         artist_id_dict={}
         return artist_id_dict
     
def send_through_kafka( track ):
    # sends data to kafka
    topic_name = 'music_top_tracks'
    track_json = json.dumps(track)
    try:
        producer.produce( topic=topic_name, key=track['song_id'], value = track_json)
        print(f"Message queued: {track['name']}")
    except Exception as e:
        print(f"Failed to send track {track['name']}: {e}")
        return

def flush_kafka_producer():
    """Flush all queued messages to Kafka."""
    producer.flush()


# -------------------------------
# API Functions
# -------------------------------
def get_top_tracks(start:int, end:int,key=key):
    """Fetch top tracks from Last.fm API for given pages."""
    track_list=[]
    for page in range(start,end):
        url= f'http://ws.audioscrobbler.com/2.0/?method=geo.getTopTracks&country=United+States&api_key={key}&format=json&page={page}'
        response= requests.get(url)
        logging.debug("API raw reponse: %s", response.text[:100])
        data=response.json()
        top_tracks=data['tracks']['track']
        track_list.extend(top_tracks)
    return track_list
        
def get_basic_data(song, count):
        """
    Extract basic track and artist information from raw Last.fm API data.

    Args:
        song (dict): Raw track data from Last.fm API.
        count (int): Current track count for rank calculation.

    Returns:
        dict: Dictionary with track name, artist name, duration, rank, listeners,
              song URL, song ID, and other basic metadata.
    """
        kafka_data= {}
        kafka_data['artist']={}
        kafka_data['artist']['stats']={}

        kafka_data['name']=song.get('name', 'N/A')
        artist_info=song.get('artist',{})
        kafka_data['artist']['name']= artist_info.get('name', 'N/A')
        kafka_data['duration']=song.get('duration', 0)
        rank = song.get('@attr', {}).get('rank', 0)
        page =math.floor((count) /50)
        kafka_data['rank'] = int(rank) + (page*50)
        kafka_data['num_song_listeners']=song.get('listeners', 0)
        kafka_data['song_url']=song.get('url', "N/A")
        kafka_data['song_id']=song.get('mbid', str(uuid.uuid4()))
        logging.info("Basic info for %s by %s retrieved", kafka_data['name'], kafka_data['artist']['name'])
        return kafka_data
    

def get_song_data(kafka_data, key=key):
        """
        Fetch detailed track information from Last.fm API and update existing data.

        Args:
            kafka_data (dict): Dictionary containing basic track and artist info.
            key (str): Last.fm API key.

        Returns:
            dict: Updated dictionary including album title and top tags.
        """
        try: 
            song_response = requests.get(f'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={key}&artist={kafka_data['artist']['name']}&track={kafka_data['name']}&format=json')
            song_response.raise_for_status()
            track_data = song_response.json().get('track', {})
            kafka_data['album_title'] = track_data.get('album', {}).get('title', 'N/A')
            toptags= track_data.get('toptags', {}).get('tag', [])
            kafka_data['tags']= [tag.get('name', 'N/A') for tag in toptags[:5]]
        except requests.RequestException as e:
            print(f"HTTP request failed for {kafka_data['name']} by {kafka_data['artist']['name']}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON for {kafka_data['name']} by {kafka_data['artist']['name']}: {e}")
            if 'song_response' in locals():
                print(f"Response text: {song_response.text[:200]}...")
            return None
        logging.info("Song info for %s has been retrieved", kafka_data['name'])
        return kafka_data

def get_artist_data(kafka_data, name,artist_id_dict, id_dict_path, key=key ):
    """
    Fetch detailed artist information from Last.fm API and update kafka_data.

    Args:
        kafka_data (dict): Dictionary with existing track and artist info.
        name (str): Artist name.
        artist_id_dict (dict): Mapping of artist names to unique IDs.
        id_dict_path (str): Path to JSON file storing artist IDs.
        key (str): Last.fm API key.

    Returns:
        dict: Updated dictionary including artist ID, on_tour, artist URL, stats,
              and similar artists list.
    """
    try:
            artist_response = requests.get(f'http://ws.audioscrobbler.com/2.0/?method=artist.getInfo&api_key={key}&artist={name}&format=json')
            if not artist_response.text.strip():
                 logging.warning(f"Empty response for artist {name}")
                 return None
            else:
                artist_data = artist_response.json()
            #print(artist_data)
            artist_specific_data=artist_data.get('artist', {})
            
            if artist_specific_data.get('name', 'N/A') !='N/A':
                 artist_name = artist_specific_data['name']
                 kafka_data['artist']['artist_id']= get_artist_id(artist_name,'N/A',artist_id_dict, id_dict_path)
            else:
                 logging.info('No artist name so we are skipping this instance')
                 return None
            kafka_data['artist']['on_tour']= artist_specific_data.get('ontour', 0)
            kafka_data['artist']['artist_url']=artist_specific_data.get('url', 'N/A')
            artist_stats= artist_specific_data.get('stats', {})
            kafka_data['artist']['stats']['artist_total_playcount']= artist_stats.get('playcount', 0)
            kafka_data['artist']['stats']['artist_total_listeners']= artist_stats.get('listeners', 0)
            similar_artists_list = artist_specific_data.get('similar',{}).get('artist', [])
            kafka_data['artist']['similar_artists'] = [artist.get('name', '') for artist in similar_artists_list]
            kafka_data['source']='Lastfm'
     
    except (requests.RequestException, json.JSONDecodeError) as e:
        track_name = kafka_data['name'] if kafka_data else 'Unknown'
        artist_name = kafka_data['artist']['name'] if kafka_data else name
        logging.error(f"HTTP request failed for {track_name} by {artist_name}: {e}")
        return None
    return kafka_data




       
        
        







# -------------------------------
# Main Execution
# -------------------------------
if __name__=='__main__':
    
    
    artist_id_filepath='artists_ids.json'
    artist_id_dict=read_id_json_file()
    fetch_interval = 86400  # Fetch new top tracks daily (24 hours)
    
    logging.info("Starting continuous Last.fm extract process")
    logging.info(f"Will fetch new top tracks daily (every {fetch_interval/3600} hours)")
    
    while True:
        try:
            count=0
            tracks= get_top_tracks(start=1, end=20)
            message_count = 0
            batch_size = 100
            
            logging.info(f"Fetching top tracks from Last.fm...")
            
            for song in tracks:
                count += 1
                data= get_basic_data(song, count)
                song_data = get_song_data(data)
                
                if not song_data:
                    logging.warning(f"Skipping {data.get('name', 'Unknown')} - failed to get song data")
                    continue
                
                artist_data = get_artist_data(song_data, song_data['artist']['name'], artist_id_dict, artist_id_filepath)
                if not artist_data:
                    logging.warning(f"Skipping {song_data.get('name', 'Unknown')} - failed to get artist data")
                    continue
                
                artist_data['rank']=count
                send_through_kafka(artist_data)
                message_count += 1
                
                if message_count % batch_size == 0:
                    flush_kafka_producer()
                    logging.info(f"Flushed {message_count} messages to Kafka")
            
            flush_kafka_producer()
            logging.info(f"Batch complete. Total messages sent: {message_count}")
            
            logging.info(f"Waiting {fetch_interval/3600} hours until next daily fetch...")
            time.sleep(fetch_interval)
            
        except KeyboardInterrupt:
            logging.info("Shutting down Last.fm extract process...")
            break
        except Exception as e:
            logging.error(f"Error in Last.fm extract: {e}")
            logging.info("Retrying in 60 seconds...")
            time.sleep(60)



 