
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
from numba.core.types import none
import requests
import json
import logging
from dotenv import load_dotenv
from src.utils.database_utils import get_db, get_null_artist_popularity
from src.utils.kafka_utils import create_producer, flush_kafka_producer, safe_batch_send
from src.utils.spotify_api_utils import get_spotify_token
import time
from src.utils.http_utils import safe_requests

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



def extract_spotify_artist_metrics(artist_id, artist_name):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    access_token=get_spotify_token()
    headers={
            'Authorization': f'Bearer {access_token}'
        }
    artists={}

    try:
        resp=resp = safe_requests("GET", url, timeout=5, headers=headers)
        resp.raise_for_status()
        if resp is None:
            logger.warning(f'No response received for artist {artist_id}')
            return None

        data= resp.json()


    except requests.exceptions.Timeout as e:
        logger.error(f'Request timeout for artist {artist_id}: {e}')
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f'Connection error for artist {artist_id}: {e}')
        return None
    except requests.HTTPError as e:
        logger.error(f'HTTP error for artist {artist_id}: {e}')
        return None
    except json.JSONDecodeError as e:
        logger.error(f'JSON decode error for artist {artist_id}: {e}')
        return None
    except Exception as e:
        logger.error(f'Unexpected error for artist {artist_id}: {e}')
        return None


    try:
        followers = data.get('followers', {})
        artists['follower_count']= followers.get('total', 0)
        artists['popularity']= data.get('popularity', 0)
        artists['artist_id']= artist_id
        artists['genres'] = data.get('genres', [])
        artists['source']= 'artist_genre'
        
        spotify_name = data.get('name')
        if spotify_name and spotify_name!= artist_name:
            artists['artist_name']= spotify_name
        else:
            artists['artist_name']= artist_name

        logger.debug(f'Extracted artist data: {artists}')

        logger.info(artists)
        required_fields= ['artist_id', 'popularity', 'follower_count', 'source', 'artist_name']
        if not all(artists.get(field) is not None  for field in required_fields):
            logger.warning(f'Incomplete data for {artist_id}')
            return None

        time.sleep(5)
        return artists


    except KeyError as e:
        logger.error(f'Key error processing artist data: {e}')
    except Exception as e:
        logger.error(f'Unexpected error processing artist data: {e}')


    



    

        



if __name__=='__main__':

    conn, cur= get_db()
    try:
        artist_id_list=get_null_artist_popularity(cur)
        artist_ids = [(artist_id[0], artist_id[1]) for artist_id in artist_id_list]
        logging.info(f'Starting the processing for {len(artist_ids)} artist ids')
        pending_batch=[]
        batch_size=20
        producer = create_producer('music_streaming_producer')
        cpu_count = multiprocessing.cpu_count()
        max_workers= min(2, cpu_count)

        with ProcessPoolExecutor(max_workers=max_workers) as w:
            futures = {w.submit(extract_spotify_artist_metrics, artist_id, artist_name): (artist_id, artist_name) for artist_id, artist_name in artist_ids}


            for future in as_completed(futures):
                artist_id = futures[future]
                try:
                    data = future.result(timeout=20)
                    if data:
                        pending_batch.append(data)
                        logger.debug(f'Extracted data for artist: {artist_id}')
                        
                        if len(pending_batch)>= batch_size:
                            success, failed = safe_batch_send(pending_batch, 'artist_genres', producer)
                            logger.info(f'Batch sent: {success} success, {failed} failed')
                            pending_batch.clear()
                    else:
                        logger.warning(f'Failed to extract data for artist: {artist_id}')

                except TimeoutError:
                    logger.error(f"Timeout processing artist {artist_id}")
                except Exception as e:
                    logger.error(f"Error processing artist {artist_id}: {e}")
            
        if pending_batch:
            success, failed = safe_batch_send(pending_batch, 'artist_genres', producer, batch_size=batch_size)
            logger.info(f'Final batch sent: {success} success, {failed} failed')
        
        flush_kafka_producer(producer)
        logger.info(f'Artist extraction completed for {len(artist_ids)} artists')
        




    finally:
        conn.close()
        cur.close()

            
