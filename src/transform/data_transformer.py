
from dotenv import load_dotenv

load_dotenv()

import logging
from src.utils.kafka_utils import consume_message, create_consumer, create_producer, flush_kafka_producer, safe_batch_send, send_through_kafka
from src.validate.artist_validator import ArtistData
from src.validate.audio_features_validator import AudioFeaturesData
from src.validate.lastfm_validator import LastFmData
from src.validate.spotify_track_validator import SpotifyTrackData
from src.utils.transformer_utils import determine_missing_fields, safe_float, safe_int, safe_string

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

release_date_precision_map={'4': 'year','7':'month', '10': 'day'}
# -------------------------------
# Transforming Functions
# -------------------------------


def transform_lastfm_data(track):
    '''Transform Lastfm data into standardized format'''
    logger.debug("Processing track: %s", track)
    logger.info("Starting to transform %s", track['song_name'])
    data={}
 
    artist_total_listeners=safe_int(track.get('artist_listeners', 0))
    num_song_listeners= safe_int(track.get('listeners',0))
    artist_total_playcount= safe_int(track.get('artist_playcount', 0))
    song_name= safe_string(track.get('original_song_name', None), lowercase=True)
    artist_name= safe_string(track.get('original_artist_name', None), lowercase=True)
    missing_req_fields = [field for field in ['song_id', 'artist_id', 'original_song_name', 'original_artist_name', 'artist_listeners', 'listeners', 'artist_playcount'] if track.get(field, None) is None]
    if missing_req_fields:
        print(f"There are missing required fields: {','.join(missing_req_fields)}")
        return None
    data['song_name'] = song_name
    data['artist_name']=artist_name
    data['artist_id']= safe_string(track.get('artist_id', None))
    data['num_song_listeners']= num_song_listeners
    data['mbid']= safe_string(track.get('mbid', None), lowercase=False)
    data['on_tour']= bool(track.get('on_tour', False))
    data['artist_total_listeners']= artist_total_listeners
    data['artist_total_playcount']= artist_total_playcount
    data['song_id']= safe_string(track.get('song_id', None))
    data['source']= safe_string(track.get('source', 'Lastfm'))
    if artist_total_listeners>0:
        if num_song_listeners>0:
            data['engagement_ratio']= round(safe_float(num_song_listeners/artist_total_listeners),5)
        if artist_total_playcount>0:
            data['plays_per_listener'] = round(safe_float(artist_total_playcount/artist_total_listeners),5)
    logger.debug("Transformed Last.fm data: %s", data)
    determine_missing_fields(data)
    return data

    

def transform_spotify_data(track):
    '''Transform Spotify data into standardized format'''
    data={}
    data['song_name']= safe_string(track.get('name', None), lowercase=True)
    data['artist_name']= safe_string(track.get('artist_name', None), lowercase=True)
    data['artist_id']= safe_string(track.get('artist_id', None))
    data['popularity']= safe_int(track.get('popularity', None))
    data['album_title']= safe_string(track.get('album_name', None), lowercase=True)
    data['album_id']= safe_string(track.get('album_id', None))
    data['song_id']= safe_string(track.get('song_id', None))
    if not all([data['song_id'],data['artist_id'], data['song_name'],data['artist_name'],data['popularity'],data['album_id'], data['album_title']]):
        logger.warning('Missing required fields, skipping track')
        return None
    if track.get('duration_ms', 0)>10800000:
        logger.warning(f"Skipping {track.get('name', 'Unknown')}, duration too long: {track.get('duration_ms', 0)}ms")
        return None
    data['album_type']= safe_string(track.get('album_type', None))
    data['is_playable']= bool(track.get('is_playable', False))
    data['release_date']= safe_string(track.get('release_date', None))
    if data['release_date']:
        data['release_date_precision']= safe_string(track.get('release_date_precision', None))
        if not data['release_date_precision']:
            data['release_date_precision']= release_date_precision_map[str(len(data['release_date']))]
    data['album_total_tracks'] = safe_int((track.get('album_total_tracks', 0)))
    data['track_number']= safe_int(track.get('track_number', 0))
    data['is_explicit']= bool(track.get('explicit', False))
    data['duration_ms']= safe_int(track.get('duration_ms', 0))
    if data['duration_ms']>0:
        data['duration_seconds']= safe_int(data['duration_ms']//1000)
        data['duration_minutes']= round(safe_float(data['duration_seconds']/60),2)
    
    
    
    data['source']= 'Spotify'
    determine_missing_fields(data)
    logger.debug("Transformed Spotify data: %s", data)
    return data



def transform_audio_features_data(track):
    '''Transform Audio Features data into standardized format'''
    data={}
    data['song_id']= safe_string(track.get('song_id', None))
    if not data['song_id']:
        logger.warning('Skipping track due to missing song_id')
        return None
    
    data['bpm']= round(safe_float(track.get('bpm', 0)),3)
    data['energy']= round(safe_float(track.get('energy', 0)),5)
    data['zero_crossing_rate']= round(safe_float(track.get('zero_crossing_rate', 0)),5)
    data['spectral_centroid'] = round(safe_float(track.get('spectral_centroid', 0)),3)
    tempo_normalized= min(data['bpm']/200, 1.0)
    data['danceability'] = round(safe_float((tempo_normalized*.3)+(data['energy']*.5)+(data['zero_crossing_rate']*.2)),5)
    data['preview_url'] = safe_string(track.get('preview_url', None)).strip()
    data['harmonic_ratio']= min(round(safe_float(track.get('harmonic_ratio', 0)),5),1.0)
    data['percussive_ratio']=min(round(safe_float(track.get('percussive_ratio', 0)),5),1.0)
    logger.debug("Percussive ratio: %s", data['percussive_ratio'])
    data['source']= safe_string(track.get('source', 'preview_url'), default='preview_url')
    logger.debug("Transformed audio features data: %s", data)
    return data


def transform_spotify_artist_data(track):
    data={}
    try:
        data['artist_id'] = safe_string(track.get('artist_id', None))
        if data['artist_id'] is None:
            logger.warning('There was no artist_id for this artist, skipping this artist')
            return None
        data['artist_name'] = safe_string(track.get('artist_name', None), lowercase=True)
        if data['artist_name'] is None:
            logger.warning('There was no artist_name for this artist, skipping this artist')
            return None
        data['followers'] = safe_int(track.get('follower_count', 0), default=0)
        if not data['followers']:
            return None
        if data['followers'] <=0:
            logger.warning('Follower count was less than or equal to 0, skipping this artist')
            return None
        data['popularity'] = safe_int(track.get('popularity', 0), default=0)
        if data['popularity'] > 100  or data['popularity'] < 0:
            logger.warning('Popularity was less than 0 or higher than 100, skipping this artist')
            return None
        data['source'] = safe_string(track.get('source'), default= 'artist_genre')
        data['genres']= track.get('genres', [])
        if not isinstance(data['genres'], list):
            logger.warning(f'Genres field is not a list for artist {data['artist_id']}')
            data['genres'] = []
        else:
            data['genres']=[safe_string(genre, lowercase=True) for genre in data['genres'] if genre and safe_string(genre)]
        data['has_genres'] = len(data['genres']) > 0
            
        logger.info("Transformed audio features data: %s", data)
        return data
    except Exception as e:
        logger.error(f'Error transforming artist data: {e}')
        return None


        




# -------------------------------
# Main ETL Loop
# -------------------------------
if __name__=='__main__':
    logger.info("Starting continuous transform process")
    consumer = create_consumer('music-streaming-consumer_2')
    producer = create_producer('music-transform-producer')

    topics=['music_top_tracks', 'music_audio_features', 'lastfm_artist', 'artist_genres']
    try:
        for topic,data in consume_message(consumer, topics):

        
            if topic == 'lastfm_artist':
                transformed_data= transform_lastfm_data(data)
                if transformed_data:
                   validated_data=LastFmData(**transformed_data)
                else:
                    continue
            elif topic =='music_audio_features':
                transformed_data = transform_audio_features_data(data)
                if transformed_data:
                    validated_data= AudioFeaturesData(**transformed_data)
                else:
                    continue
            elif topic=='music_top_tracks':
                transformed_data= transform_spotify_data(data)
                if transformed_data:
                    validated_data = SpotifyTrackData(**transformed_data)
                else:
                    continue
            elif topic=='artist_genres':
                transformed_data = transform_spotify_artist_data(data)
                if transformed_data:
                    validated_data = ArtistData(**transformed_data)
                else:
                    continue
            success, failed=safe_batch_send([transformed_data], 'music_transformed', producer, batch_size=5)
            logger.info(f'Batch was sent with {success} successful tracks/artists/audio_features sent and {failed} failed')
    

        
    finally:
        logger.info("Data transformation process completed")
        consumer.close()
        flush_kafka_producer(producer)




