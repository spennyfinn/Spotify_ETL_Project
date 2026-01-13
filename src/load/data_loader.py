

from config.logging import error_logger
import psycopg2
from dotenv import load_dotenv
import logging

from src.utils.database_utils import get_db
from src.utils.kafka_utils import consume_message, create_consumer
from src.load.parsers import parse_audio_features_data, parse_lastfm_message, parse_spotify_message
from src.utils.spotify_api_utils import  spotify_album_query, spotify_artist_query, spotify_song_query, lastfm_artist_query, lastfm_song_query, insert_audio_features_query


load_dotenv()
logger= logging.getLogger(__name__)

# -------------------------------
# Logging Configs
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
 
def load_lastfm_data_batch(lastfm_batch, cur):
    success_count=0
    error_count=0
    artist_batch = []
    song_batch=[]
    for message in lastfm_batch:
        try:
            song, artist  = parse_lastfm_message(message)
            artist_name = artist[0]
            artist_batch.append(artist)
            song_batch.append(song)
        except Exception as e:
            error_logger.error(f"Failed to parse Last.fm message: {e}", extra={'operation': 'lastfm_parse', 'message': str(message)[:200]})
            error_count+=1
            continue
    if artist_batch:
        try:
            # Insert artist and album first
            cur.executemany(lastfm_artist_query, artist_batch)
            logging.info(f"Artist batch loaded/updated: {len(artist_name)}")
            success_count+=len(artist_batch)
        except psycopg2.IntegrityError as e:
            error_logger.error(f"Failed to load batch from lastfm: {e}")
            
            for artist in artist_batch:
                try: 
                    cur.execute(lastfm_artist_query, artist)
                    success_count+=1
                except Exception as e:
                    error_logger.error(f"Failed to load artist: {e}")
                    error_count+=1

    # Insert the song '
    if song_batch:
        try:
            cur.executemany(lastfm_song_query, song_batch)
            logging.info(f"Song batch loaded/updated: {len(song_batch)}")
            success_count+=len(song_batch)
        except psycopg2.IntegrityError as e:
                error_logger.error(f"Failed to load song batch: {e}")

                for song in song_batch:
                    try:
                        cur.execute(lastfm_song_query, song)
                        success_count+=1
                    except Exception as e:
                        error_logger.error(f"Failed individual song insert: {e}")
                        error_count+=1
               
    return success_count, error_count


def load_spotify_data_batch(songs,cur):
    success_count=0
    error_count=0
    song_batch=[]
    artist_batch=[]
    album_batch=[]
    for message in songs:
        song, album, artist= parse_spotify_message(message)
        if not song[0] or not song[1]:
            error_logger.error(f"NULL values detected: song_name={song[0]}, artist_id={song[1]}",
                extra={'operation': 'spotify_null_check', 'song_name': song[0], 'artist_id': song[1]})
            error_count+=1
            continue
        song_batch.append(song)
        album_batch.append(album)
        artist_batch.append(artist)
        

    if artist_batch:
        try:
            cur.executemany(spotify_artist_query, artist_batch)
            logging.info(f'Spotify artist data batch inserted')
            success_count+=len(artist_batch)
        except Exception as e:
            error_logger.error(f"Failed to insert Spotify artist data batch {e}")
            for artist in artist_batch:
                try:
                    cur.execute(spotify_artist_query, artist)
                    success_count+=1
                except Exception as e:
                    error_logger.error(f"Failed to insert Spotify artist: {e}")
                    error_count+=1
    if album_batch:
        try:
            cur.executemany(spotify_album_query, album_batch)
            logging.info(f'Spotify artist data inserted: {album[0]}')
            success_count+=len(album_batch)
        except Exception as e:
            error_logger.error(f"Failed to insert Spotify album batch: {e}")
            error_count+=1

            for album in album_batch:
                try:
                    cur.execute(spotify_album_query, album)
                    success_count+=1
                except Exception as e:
                    error_logger.error(f"Failed to insert Spotify album: {e}")
                    error_count+=1
    if song_batch: 
        logger.debug(f'Song batch: {song_batch}')
        try:
            cur.executemany(spotify_song_query, song_batch)
            logging.info(f'Spotify song batch inserted')
            success_count+=len(song_batch)
        except Exception as e:
            error_logger.error(f"Failed to insert Spotify song batch: {e}")

            for song in song_batch:
                try:
                    cur.execute(spotify_song_query, song)
                    success_count+=1
                except Exception as e:
                    error_logger.error(f"Failed to insert Spotify song: {e}")
                    error_count+=1

    
    return success_count, error_count

def load_audio_features_batch(batch, cur):
    success_count =0
    error_count=0
    audio_batch=[]

    for message in batch:
        try:
            audio_features = parse_audio_features_data(message)
            audio_batch.append(audio_features)
        except Exception as e:
            error_logger.error('Failed to parse audio feature data: {e}')
            error_count+=1
        continue
    if audio_batch:
        try:
            cur.executemany(insert_audio_features_query, audio_batch)
            logging.info(f"Audio features loaded")
            success_count+=len(audio_features)
        except Exception as e:
            error_logger.error(f"Failed to load audio features: {e}")
            for feature in audio_batch:
                try:
                    cur.execute(insert_audio_features_query, feature)
                    success_count+=1
                except Exception as e:
                    error_logger.error(f'Failed to load individual song: {e}')
                    error_count+=1

    return success_count, error_count
                

            
        




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

        lastfm_batch=[]
        spotify_batch=[]
        audio_batch=[]
        batch_size=10

        try:
            for message in consume_message(consumer, ['music_transformed']):
            
                message= message[1]
                logger.debug(f'ETL message: {message}')
                if message['source']== 'Lastfm':
                    lastfm_batch.append(message)
                    if len(lastfm_batch)>= batch_size:
                        success, errors= load_lastfm_data_batch(lastfm_batch, cur)
                        success_count+=success
                        lastfm_count+=success
                        errors_count+=errors
                        lastfm_batch=[]
                        logging.info(f"Processed Lastfm batch: {success} success, {errors} errors")
                elif message['source']=='Spotify':
                    spotify_batch.append(message)
                    if len(spotify_batch)>= batch_size:
                        success, errors= load_spotify_data_batch(spotify_batch, cur)
                        success_count+=success
                        spotify_count+=success
                        errors_count+=errors
                        spotify_batch=[]
                        logging.info(f"Processed Spotify batch: {success} success, {errors} errors")
                elif message['source']=='preview_url':
                    audio_batch.append(message)
                    if len(audio_batch)>= batch_size:
                        success, errors=  load_audio_features_batch(audio_batch, cur)
                        success_count+=success
                        audio_features_count+=success
                        errors_count+=errors
                        audio_batch=[]
                        logging.info(f"Processed audio features batch: {success} success, {errors} errors")
                    
                else:
                    error_logger.error(f"Unknown message source: {message.get('source', 'Unknown')}",
                    extra={'operation': 'message_processing', 'message_source': message.get('source', 'unknown'),
                            'message_keys': list(message.keys()) if isinstance(message, dict) else 'not_dict'})
                    error_count+=1

            if lastfm_batch:
                success, errors = load_lastfm_data_batch(lastfm_batch, cur)
                success_count+=success
                lastfm_count += success
                errors_count += errors
                logging.info(f"Processed final Last.fm batch: {success} success, {errors} errors")

            if spotify_batch:
                success, errors = load_spotify_data_batch(spotify_batch, cur)
                spotify_count += success
                success_count+=success
                errors_count += errors
                logging.info(f"Processed final Spotify batch: {success} success, {errors} errors")

            if audio_batch:
                success, errors = load_audio_features_batch(audio_batch, cur)
                audio_features_count += success
                errors_count += errors
                success_count+=success
                logging.info(f"Processed final Audio batch: {success} success, {errors} errors")
            
            logging.info("=" * 60)
            logging.info("ETL PROCESS STATUS - SUMMARY")
            logging.info("=" * 60)
            logging.info(f"Last.fm records processed: {lastfm_count}")
            logging.info(f"Spotify records processed: {spotify_count}")
            logging.info(f"Audio Feature records processed: {audio_features_count}")
            logging.info(f"Total records processed: {lastfm_count + spotify_count + audio_features_count}")
            logging.info(f"Errors encountered: {errors_count}")
            logging.info("=" * 60) 
        except KeyboardInterrupt:
            logging.info("ETL interrupted by user")
        except Exception as e:
            error_logger.error(f"ETL process failed: {e}")
    finally:
        conn.commit()
        cur.close()
        conn.close()
                
       
                


                
            
                
   


