
from tarfile import data_filter
from confluent_kafka import Consumer, Producer
import json
import uuid

from numba import none
from Load_Music import consume_message
from pydantic import ValidationError 
from Validation_Classes.Validation_Class_Audio_Features import audio_features
from Validation_Classes.Validation_Class_Lastfm import Last_fm_data
from Validation_Classes.Validation_Class_Spotify import Spotify_Data
import logging
from Extract_Lastfm_Data import get_artist_id, read_id_json_file



logging.basicConfig(level=logging.INFO, format="%(message)s")


# -------------------------------
# Kafka Configurations
# -------------------------------
consumer_config= {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'music-streaming-consumer_2',
    'auto.offset.reset':'earliest',
}
producer_config = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'music-transform-producer'
}


# -------------------------------
# Utility Function(s)
# -------------------------------
def normalize_str(string:str)-> str:
    '''
    Normalizes a string to all lowercase characters and removes whitespace

    Args:
        string (string): A string to format
    
    Returns:
        string: a lowercase string without whitespace
    '''
    if not string:
        return ""
    else:
        return str(string).lower().strip()


    

# -------------------------------
# Transforming Function
# -------------------------------
def transform_data(track):
    '''
    Transform raw track data into a standardized format.

    Args:
        track (dict): Raw track data from Kafka

    Returns:
        dict: Transformed track data
        None: If essential fields (song or artist name) are missing
    '''
    
    
    print(track)
    
    # Validate track has required 'source' field
    if not track or 'source' not in track:
        logging.warning("Track missing 'source' field, skipping")
        return None
    
    data={}
    if track['source']=='Lastfm':
        logging.info("Starting to transform %s", track['name'])
        # specifying a nested list for easier lookup later
        artist_dict =track.get('artist', {})

        # song and artist name
        song_name=track['name']
        artist_name =  artist_dict['name']

        # the song name or artist name are missing skip, else store the data 
        if song_name != 'N/A' and artist_name!='N/A':
            data['song_name']= normalize_str(song_name)
            data['artist_name'] = normalize_str(artist_name)
        else:
            return None

        data['rank']= track['rank']
        data['duration_seconds']= int(track['duration'])
        data['num_song_listeners']= int(track['num_song_listeners'])

        #handle missing values in song_id
        song_id= normalize_str(track['song_id'])
        if song_id == 'n/a':
            data['song_id'] = str(uuid.uuid4())
        else:
            data['song_id']= song_id  

        data['song_url']=normalize_str(track['song_url'])
        data['artist_id']= normalize_str(artist_dict['artist_id'])
        data['artist_url']= artist_dict['artist_url']
        data['album_title'] = normalize_str(track['album_title'])
        
        # Validate tags is a list before iterating
        tags = track.get('tags', [])
        if not isinstance(tags, list):
            logging.warning(f"Tags is not a list for {track.get('name', 'Unknown')}, using empty list")
            tags = []
        data['tags']=[normalize_str(tag)for tag in tags]
        
        # Validate similar_artists is a list before iterating
        similar_artists = artist_dict.get('similar_artists', [])
        if not isinstance(similar_artists, list):
            logging.warning(f"Similar artists is not a list for {track.get('name', 'Unknown')}, using empty list")
            similar_artists = []
        data['similar_artists']= [normalize_str(artist) for artist in similar_artists]
        data['on_tour']= bool(int(track['artist']['on_tour']))
    

        data['artist_total_playcount']= int(artist_dict['stats']['artist_total_playcount'])
        data['artist_total_listeners']= int(artist_dict['stats']['artist_total_listeners'])
        data['duration_minutes'] = round((data['duration_seconds']/60),2)
        #division safety check
        listeners = data.get('artist_total_listeners',1)
        data['plays_per_listener']= round(data['artist_total_playcount']/listeners,5)
        data['engagement_ratio'] = round(data['num_song_listeners'] / listeners,5)
        data['source']= 'Lastfm'
        logging.info("Transformation is finished for %s", track['name'])
        
    elif track['source']=='Spotify':
        data['album_type']= str(track['album_type'])
        data['is_playable']= bool(track['is_playable'])
        data['album_title']= normalize_str(track['album_name'])
        data['album_id']= str(track['album_id'])
        data['song_name']= normalize_str(track['name'])
        data['artist_name']= normalize_str(track['artist_name'])
        data['release_date']= str(track['release_date'])
        data['release_date_precision']= str(track['release_date_precision'])
        data['album_total_tracks'] = int(track['album_total_tracks'])
        data['track_number']= int(track['track_number'])
        data['is_explicit']= bool(track['explicit'])
        data['popularity']=int(track['popularity'])
        data['duration_ms']= int(track['duration_ms'])
        data['duration_seconds']= data['duration_ms']//1000
        data['duration_minutes']= round(data['duration_seconds']/60,2)
        data['song_id']= str(track['song_id'])
        artist_id_dict= read_id_json_file()
        data['artist_id']= str(get_artist_id(data['artist_name'],'N/A',artist_id_dict,'artist_id.json'))
        data['source']= 'Spotify'
        print(data)
    elif track['source']== 'preview_url':
        
        data['song_name'] = track.get('name', None)
        data['artist_id'] = track.get('artist_id', None)
        if not data['song_name'] or not data['artist_id']:
            print('Skipping this track due to the lack of a song_name or artist_name')
            return None
        data['song_id']= str(track.get('song_id', None))
        data['bpm']= round(float(track.get('bpm', 0)),3)
        data['energy']= round(float(track.get('energy', 0)),5)
        data['zero_crossing_rate']= round(float(track.get('zero_crossing_rate', 0)),5)
        data['spectral_centroid'] = round(float(track.get('spectral_centroid', 0)),3)
        data['preview_url'] = str(track.get('preview_url', None)).strip()
        data['harmonic_ratio']= round(float(track.get('harmonic_ratio', 0)),5)
        data['percussive_ratio']=round(float(track.get('percussive_ratio', 0)),5)


        tempo_normalized= min(data['bpm']/200, 1.0)
        data['danceability'] = round((tempo_normalized*.3)+(data['energy']*.5)+(data['zero_crossing_rate']*.2),5)
        data['source']= track.get('source', 'preview_url')
        print(data)
    return data
        


        







# -------------------------------
# Main ETL Loop
# -------------------------------
if __name__=='__main__':
    logging.info("Starting continuous transform process")
    
    try:
        consumer = Consumer(consumer_config)
        producer = Producer(producer_config)

        message_count = 0
        batch_size = 1
        
        for track in consume_message(consumer, 'music_top_tracks'):
            data= transform_data(track)
            
            # Check if data is None before accessing
            if not data:
                logging.warning("Transform returned None, skipping")
                continue
            
            if data['source']=='Lastfm':
                try: 
                    validated_data=Last_fm_data(**data)
                except ValidationError as e:
                    print(f'Validation Error: {e}')
                    continue
            elif data['source']=='Spotify':
                try: 
                    validated_data=Spotify_Data(**data)
                except ValidationError as e:
                    print(f'Validation Error: {e}')
                    continue
            elif data['source']=='preview_url':
                try:
                    validated_data = audio_features(**data)
                except ValidationError as e:
                    print(f'Validation Error: {e}')
                    continue
            
            producer.produce(
                topic= 'music_transformed',
                key= data['song_id'],
                value= json.dumps(data)
            )
            message_count += 1
            
            # Batch flush for efficiency
            if message_count % batch_size == 0:
                producer.flush()
                logging.info(f"Flushed {message_count} messages to Kafka")
        
        # Final flush for remaining messages
        producer.flush()
        logging.info(f"Transform complete. Total messages sent: {message_count}")

    finally:
        consumer.close()




