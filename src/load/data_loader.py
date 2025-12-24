
from confluent_kafka import Consumer
import psycopg2
from dotenv import load_dotenv
import logging
from src.utils.database import get_db
from src.utils.kafka_utils import consume_message, create_consumer
from src.load.parsers import parse_audio_features_data, parse_lastfm_message, parse_spotify_message


load_dotenv()


# -------------------------------
# Logging Configs
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# -------------------------------
# SQL Queries
# -------------------------------
lastfm_song_query = ("INSERT INTO songs(song_name,song_id, song_listeners, artist_id, song_url,mbid,engagement_ratio) "
                 "VALUES (%s, %s, %s, %s, %s, %s,%s) "
                 "ON CONFLICT (song_name, artist_id) DO UPDATE SET "
                 "song_listeners = EXCLUDED.song_listeners, "
                 "song_url = EXCLUDED.song_url, "
                 "engagement_ratio = EXCLUDED.engagement_ratio;")
                 
lastfm_artist_query = ("INSERT INTO artists(artist_name,artist_id, on_tour, total_listeners, total_playcount, plays_per_listener) "
            "VALUES (%s,%s, %s, %s, %s, %s) "
            "ON CONFLICT (artist_id) DO UPDATE "
            "SET on_tour = EXCLUDED.on_tour, "
            "total_listeners = EXCLUDED.total_listeners,"
            "total_playcount = EXCLUDED.total_playcount,"
            "plays_per_listener=EXCLUDED.plays_per_listener;")

'''
lastfm_album_query = ("INSERT INTO albums(album_id, album_title, artist_name) "
            "VALUES (%s,%s, %s) "
            "ON CONFLICT (album_title, artist_name) DO UPDATE "
            "SET album_id = EXCLUDED.album_id " \
            "RETURNING album_id; "
            )

lastfm_tags_query = ("INSERT INTO tags(song_name,artist_id,tag) "
            "VALUES (%s,%s, %s) "
            "ON CONFLICT (song_name, artist_id,tag) DO NOTHING; "
            )
lastfm_similar_artist_query =("INSERT INTO similar_artists(artist_name, similar_artist_name) "
            "VALUES (%s, %s) "
            "ON CONFLICT (artist_name, similar_artist_name) DO NOTHING ;"
            )'''

spotify_song_query=('INSERT INTO songs(song_name, artist_id, duration_ms, duration_seconds, duration_minutes, release_date, release_date_precision, is_explicit, popularity, track_number, song_id, album_id, is_playable) '
                   'VALUES(%s,%s,%s ,%s,%s,%s,%s,%s,%s,%s, %s, %s, %s) ' \
                   'ON CONFLICT ON CONSTRAINT songs_pkey '
                   'DO UPDATE ' \
                    'SET duration_seconds = EXCLUDED.duration_seconds,' \
                    'duration_minutes = EXCLUDED.duration_minutes,' \
                    'duration_ms= EXCLUDED.duration_ms,' \
                    'release_date = EXCLUDED.release_date,' \
                    'release_date_precision=EXCLUDED.release_date_precision,' \
                    'is_explicit=EXCLUDED.is_explicit,' \
                    'popularity= EXCLUDED.popularity,' \
                    'track_number= EXCLUDED.track_number,' \
                    'is_playable = EXCLUDED.is_playable;'
                   )
spotify_album_query=('INSERT INTO albums(album_title, artist_name, album_type, album_total_tracks, album_id) '
                    'VALUES(%s,%s,%s,%s,%s) '
                    'ON CONFLICT (album_id) DO UPDATE '
                    'SET album_type = EXCLUDED.album_type,'
                    'album_total_tracks = EXCLUDED.album_total_tracks')

spotify_artist_query=('INSERT INTO artists(artist_id, artist_name) '
                      'VALUES(%s,%s) '
                      'ON CONFLICT (artist_id) DO UPDATE SET '
                      'artist_name = EXCLUDED.artist_name;')


insert_audio_features_query= ('INSERT INTO song_audio_features(song_name, artist_id, bpm, energy, spectral_centroid, zero_crossing_rate, danceability, preview_url, harmonic_ratio, percussive_ratio) '
                              'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '
                              'ON CONFLICT (song_name, artist_id) DO UPDATE SET '
                              'bpm = EXCLUDED.bpm, '
                              'energy = EXCLUDED.energy, '
                              'spectral_centroid = EXCLUDED.spectral_centroid, '
                              'zero_crossing_rate = EXCLUDED.zero_crossing_rate, '
                              'danceability = EXCLUDED.danceability, '
                              'preview_url = EXCLUDED.preview_url, '
                              'harmonic_ratio = EXCLUDED.harmonic_ratio, '
                              'percussive_ratio = EXCLUDED.percussive_ratio;'
)


def load_last_fm(message, cur):
    song, artist  = parse_lastfm_message(message)
    song_name = song[0]
    artist_name = artist[1]
    
    try:
        # Insert artist and album first
        cur.execute(lastfm_artist_query, artist)
        logging.info(f"Artist loaded/updated: {artist_name}")
    except psycopg2.IntegrityError as e:
        logging.error(f"Failed to load {artist_name}: {e}")
        return False

    # Insert the song 
    try:
        cur.execute(lastfm_song_query, song)
        logging.info(f"Song loaded/updated: {song_name} by {artist_name}")
    except psycopg2.IntegrityError as e:
            logging.error(f"Failed to load song {song_name} by {artist_name}: {e}")
            return False
    
    return True

def load_spotify_data(message,cur):
    song, album, artist= parse_spotify_message(message)
    song_name = song[0]
    artist_name=artist[1]

            
    # Add this debug logging:
    logging.info(f"DEBUG - Song data: song_name='{song[0]}', artist_id='{song[1]}', song_id='{song[10]}, album_id='{album[4]}'")
    if not song[0] or not song[1]:
        logging.error(f"NULL values detected: song_name={song[0]}, artist_id={song[1]}")
        return False

    try:
        cur.execute(spotify_artist_query, artist)
        logging.info(f'Spotify artist data inserted: {song_name} by {artist_name}')
        cur.execute(spotify_album_query, album)
        logging.info(f'Spotify artist data inserted: {album[0]} by {artist_name} for {song_name}')
        cur.execute(spotify_song_query, song)
        logging.info(f"Spotify song data inserted: {song_name} by {artist_name}")
    except Exception as e:
        logging.error(f"Failed to insert Spotify song data for {song_name} by {artist_name}: {e}")
        return False
            
    # Try to insert/update album, handling potential album_id conflicts
    try:
        
        logging.info(f"✓ Spotify album data inserted: {album[0]} by {artist_name}")
    except psycopg2.IntegrityError as e:
        logging.error(f"Failed to insert Spotify album data for {album[0]} by {artist_name}: {e}")
       
        return False
    
    return True

def load_audio_features(message, cur):
    try:
        audio_features = parse_audio_features_data(message)
        cur.execute(insert_audio_features_query, audio_features)
        logging.info(f"Audio features loaded for: {message.get('song_name', 'Unknown')}")
        return True
    except Exception as e:
        logging.error(f"Failed to load audio features: {e}")
        return False




# -------------------------------
# Main ETL Loop
# -------------------------------
if __name__=='__main__':
    conn,cur=get_db()
    consumer = create_consumer('music-streaming-consumer_v2')
    try:
        logging.info("Starting continuous ETL process - loading music data into database")

        lastfm_count=0
        spotify_count=0
        audio_features_count=0
        success_count=0
        errors_count = 0

        for message in consume_message(consumer, ['music_transformed']):
           
            message= message[1]
            if message['source']== 'Lastfm':
                res=load_last_fm(message,cur)
                if not res:
                    error_count+=1
                else:
                    lastfm_count_count+=1
                


            elif message['source']=='Spotify':
                res=load_spotify_data(message,cur)
                if not res:
                    error_count+=1
                else:
                    spotify_count+=1
                
            elif message['source']=='preview_url':
                res=load_audio_features(message,cur)
                if not res:
                    error_count+=1
                else:
                    audio_features_count_count+=1


                
                # Summary statistics
                logging.info("=" * 60)
                logging.info("ETL PROCESS STATUS - SUMMARY")
                logging.info("=" * 60)
                logging.info(f"Last.fm records processed: {lastfm_count}")
                logging.info(f"Spotify records processed: {spotify_count}")
                logging.info(f"Audio Feature records processed: {audio_features_count}")
                logging.info(f"Total records processed: {lastfm_count + spotify_count + audio_features_count}")
                logging.info(f"Errors encountered: {errors_count}")
                logging.info("=" * 60)
                
                
    finally:
        cur.close()
        conn.close()
        consumer.close()
        logging.info("Database connections and consumer closed")


