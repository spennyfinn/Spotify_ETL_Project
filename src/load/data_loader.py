
from src.logging_config import error_logger
import psycopg2
from dotenv import load_dotenv
import logging
from datetime import datetime
from src.utils.database import get_db
from src.utils.kafka_utils import consume_message, create_consumer
from src.load.parsers import parse_audio_features_data, parse_lastfm_message, parse_spotify_message
from src.utils.spotify_utils import insert_spotify_artists, spotify_album_query, spotify_song_query, lastfm_artist_query, lastfm_song_query, insert_audio_features_query


load_dotenv()


# -------------------------------
# Logging Configs
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_last_fm(message, cur):
    
    song, artist  = parse_lastfm_message(message)
    song_name = song[0]
    artist_name = artist[0]
    print(f'{song_name}, {artist_name}')
    
    try:
        # Insert artist and album first
        cur.execute(lastfm_artist_query, artist)
        logging.info(f"Artist loaded/updated: {artist_name}")
    except psycopg2.IntegrityError as e:
        error_logger.error(f"Failed to load {artist_name}: {e}",
            extra={'operation': 'lastfm_artist_insert', 'artist_name': artist_name, 'error_type': type(e).__name__})
        return False

    # Insert the song 
    try:
        cur.execute(lastfm_song_query, song)
        logging.info(f"Song loaded/updated: {song_name} by {artist_name}")
    except psycopg2.IntegrityError as e:
            error_logger.error(f"Failed to load song {song_name} by {artist_name}: {e}",
                extra={'operation': 'lastfm_song_insert', 'song_name': song_name, 'artist_name': artist_name, 'error_type': type(e).__name__})
            return False
    
    return True

def load_spotify_data(message,cur):
    song, album, artist= parse_spotify_message(message)
    print(f'SOng:{song}')
    print(album)
    print(artist)
    song_name = song[0]
    print(song_name)
    artist_name=artist[1]
    print(artist_name)
            
    if not song[0] or not song[1]:
        error_logger.error(f"NULL values detected: song_name={song[0]}, artist_id={song[1]}",
            extra={'operation': 'spotify_null_check', 'song_name': song[0], 'artist_id': song[1]})
        return False

    try:
        insert_spotify_artists(artist,cur)
        logging.info(f'Spotify artist data inserted: {song_name} by {artist_name}')
    except Exception as e:
        error_logger.error(f"Failed to insert Spotify artist data for {song_name} by {artist_name}: {e}",
            extra={'operation': 'spotify_artist_insert', 'song_name': song_name, 'artist_name': artist_name, 'error_type': type(e).__name__})
        return False
    try:
        cur.execute(spotify_album_query, album)
        logging.info(f'Spotify artist data inserted: {album[0]} by {artist_name} for {song_name}')
    except Exception as e:
        error_logger.error(f"Failed to insert Spotify album data for {song_name} by {artist_name}: {e}",
            extra={'operation': 'spotify_album_insert', 'song_name': song_name, 'artist_name': artist_name, 'error_type': type(e).__name__})
        return False
    try:
        cur.execute(spotify_song_query, song)
        logging.info(f"Spotify song data inserted: {song_name} by {artist_name}")
    except Exception as e:
        error_logger.error(f"Failed to insert Spotify song data for {song_name} by {artist_name}: {e}",
            extra={'operation': 'spotify_song_insert', 'song_name': song_name, 'artist_name': artist_name, 'error_type': type(e).__name__})
        return False
    
            
    # Try to insert/update album, handling potential album_id conflicts
    try:
        
        logging.info(f"✓ Spotify album data inserted: {album[0]} by {artist_name}")
    except psycopg2.IntegrityError as e:
        error_logger.error(f"Failed to insert Spotify album data for {album[0]} by {artist_name}: {e}",
            extra={'operation': 'spotify_album_insert', 'album_title': album[0], 'artist_name': artist_name, 'error_type': type(e).__name__})

        return False
    
    return True

def load_audio_features(message, cur):
    try:
        audio_features = parse_audio_features_data(message)
        cur.execute(insert_audio_features_query, audio_features)
        logging.info(f"Audio features loaded for song_id: {message.get('song_id', 'Unknown')}")
        return True
    except Exception as e:
        error_logger.error(f"Failed to load audio features: {e}",
            extra={'operation': 'audio_features_insert', 'song_id': message.get('song_id', 'unknown'), 'error_type': type(e).__name__})
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
            print(message)

            try:
                if message['source']== 'Lastfm':
                    res=load_last_fm(message,cur)
                    if not res:
                        errors_count+=1
                    else:
                        lastfm_count+=1

                    


                elif message['source']=='Spotify':
                    res=load_spotify_data(message,cur)
                    if not res:
                        errors_count+=1
                    else:
                        spotify_count+=1
                    
                elif message['source']=='preview_url':
                    res=load_audio_features(message,cur)
                    if not res:
                        errors_count+=1
                    else:
                        audio_features_count+=1
                else:
                    error_logger.error(f"Unknown message source: {message.get('source', 'Unknown')}",
                    extra={'operation': 'message_processing', 'message_source': message.get('source', 'unknown'),
                            'message_keys': list(message.keys()) if isinstance(message, dict) else 'not_dict'})
                    error_count+=1
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
            except Exception as e:
                error_logger.error(f'An error occurred while processing the message: {e}',extra={
                        'operation': 'message_processing','message_source': message.get('source', 'unknown') if isinstance(message, dict) else 'not_dict',
                        'error_type': type(e).__name__, 'error_details': str(e)
                    } )
                error_count+=1
                continue
            


                
            
                
                
    finally:
        cur.close()
        conn.close()
        consumer.close()
        logging.info("Database connections and consumer closed")


