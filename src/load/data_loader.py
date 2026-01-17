

from config.logging import error_logger
import psycopg2
from dotenv import load_dotenv
import logging

from src.utils.database_utils import get_db
from src.utils.kafka_utils import consume_message, create_consumer
from src.load.parsers import parse_artist_data, parse_audio_features_data, parse_lastfm_message, parse_spotify_message
from src.utils.spotify_api_utils import  insert_artist_data_query, insert_genres_query, spotify_album_query, spotify_artist_query, spotify_song_query, lastfm_artist_query, lastfm_song_query, insert_audio_features_query


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
            error_logger.error(f"Failed to parse Last.fm message: {e}", extra={'operation': 'lastfm_parse', 'raw_message': str(message)[:200]})
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

def load_artist_data_batch(batch, cur):
    artist_success_count=0
    artist_error_count=0
    genre_success_count=0
    genre_error_count=0
    artist_genre_success_count=0
    artist_genre_error_count=0
    artist_batch=[]
    genres_batch=[]
    artist_genres_batch=[]

    for message in batch:
        try:
            artists, genres, artist_genres=parse_artist_data(message)
            artist_batch.append(artists)
            genres_batch.append(genres)
            artist_genres_batch.append(artist_genres)
        except Exception as e:
            error_logger.error("There was an error while parsing the spotify artist data: {e}")
            continue
    if artist_batch:
        try:
            cur.executemany(insert_artist_data_query, artist_batch)
            artist_success_count += len(artist_batch)
        except Exception as e:
            error_logger.error(f'There was an error while inserting the artist batch: {e}')
            for message in artist_batch:
                try:
                    cur.execute(insert_artist_data_query, message)
                    artist_success_count+=1
                except Exception as e:
                    error_logger.error(f'Failed to insert artist with id: {message[0]}')
                    artist_error_count+=1
    if genres_batch:
        for genre_list in genres_batch:
            try:
                cur.executemany(insert_genres_query, genre_list)
                genre_success_count+=len(genre_list)
            except Exception as e:
                error_logger.error(f'There was an error while inserting the genre batch: {e}')
                for genre in genre_list:
                    try:
                        cur.execute(insert_genres_query, genre)
                        genre_success_count+=1
                    except Exception as e:
                        error_logger.error(f'Failed to insert genre {genre[0]}')
                        genre_error_count+=1
    if artist_genres_batch:
        try:
            all_genre_names = set()
            for artist_genre_list in artist_genres_batch:
                for artist_genre in artist_genre_list:
                    try:
                        genre_name = artist_genre[1]
                        if genre_name and genre_name.strip():
                            all_genre_names.add(genre_name.strip())
                    except (IndexError, TypeError) as e:
                        continue
            logger.info(f'Collected {len(all_genre_names)} unique genres for processing')

        except Exception as e:
            error_logger.error(f'Failed to collect genre names: {e}')
            all_genre_names = set()
       
        if all_genre_names:
            try:
                placeholders= ','.join(['%s']*len(all_genre_names))
                cur.execute(f'SELECT genre_name, genre_id FROM genres WHERE genre_name IN ({placeholders})', list(all_genre_names))
                genre_name_to_id = dict(cur.fetchall())
                logger.info(f'Retrieved {len(genre_name_to_id)} genre_ids')
            except Exception as e:
                error_logger.error(f'Failed to query genre_ids: {e}')
    
        for artist_genre_list in artist_genres_batch:
            for artist_genre in artist_genre_list:
                try:
                    artist_id, genre_name = artist_genre
                    genre_id = genre_name_to_id.get(genre_name)
                    if genre_id:
                        cur.execute('INSERT INTO artist_genres (artist_id, genre_id) '
                                    'VALUES (%s,%s) '
                                    'ON CONFLICT (artist_id, genre_id) DO NOTHING;', (artist_id, genre_id))
                        artist_genre_success_count+=1
                    else:
                        artist_genre_error_count+=1
                except Exception as e:
                    error_logger.error(f'Failed to insert artist_genre {artist_genre}: {e}')
                    artist_genres_error_count += 1


    return artist_success_count, artist_error_count,genre_success_count,genre_error_count,artist_genre_success_count,artist_genre_error_count


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
        artist_count=0
        success_count=0
        errors_count = 0

        lastfm_batch=[]
        spotify_batch=[]
        audio_batch=[]
        artist_batch=[]
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
                elif message['source']== 'artist_genre':
                    artist_batch.append(message)
                    if len(artist_batch)>= batch_size:
                        logging.info(f"Processing artist batch of {len(artist_batch)} records")
                        a_success, a_error, g_success, g_error, ag_success, ag_error = load_artist_data_batch(artist_batch, cur)
                        success= a_success+g_success+ag_success
                        errors= a_error+g_error+ag_error

                        logging.info(f"Artist batch results: Artists({a_success}/{a_error}) | Genres({g_success}/{g_error}) | Relationships({ag_success}/{ag_error}) | Total({success}/{errors})")

                        artist_count += success
                        errors_count += errors
                        success_count+=success
                        artist_batch=[]
                    
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

            if artist_batch:
                logging.info(f"Processing final artist batch of {len(artist_batch)} records")
                a_success, a_error, g_success, g_error, ag_success, ag_error = load_artist_data_batch(artist_batch, cur)
                success= a_success+g_success+ag_success
                errors= a_error+g_error+ ag_error

                logging.info(f"Final artist batch results: Artists({a_success}/{a_error}) | Genres({g_success}/{g_error}) | Relationships({ag_success}/{ag_error}) | Total({success}/{errors})")

                artist_count += success
                errors_count += errors
                success_count+=success

            logging.info("=" * 60)
            logging.info("ETL PROCESS STATUS - SUMMARY")
            logging.info("=" * 60)
            logging.info(f"Last.fm records processed: {lastfm_count}")
            logging.info(f"Spotify records processed: {spotify_count}")
            logging.info(f"Audio Feature records processed: {audio_features_count}")
            logging.info(f"Artist Data records processed: {artist_count}")
            logging.info(f"Total records processed: {lastfm_count + spotify_count + artist_count+audio_features_count}")
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
                
       
                


                
            
                
   


