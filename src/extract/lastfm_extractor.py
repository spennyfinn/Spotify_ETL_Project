
import requests
import os
import json
import logging
from src.utils.kafka_utils import create_producer, flush_kafka_producer, safe_batch_send, send_through_kafka
from src.utils.text_processing_utils import normalize_song_name, similarity_score
from src.utils.database_utils import get_db
from dotenv import load_dotenv
import random
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError

logger = logging.getLogger(__name__)

def get_track_from_lastfm(song_name, artist_name, song_id,artist_id, key):

    song_name_normalized= normalize_song_name(song_name)
    artist_name_normalized=normalize_song_name(artist_name)
   

    #define url parameters
    query = f"{song_name_normalized} {artist_name_normalized}"
    
    
    #call API with exception handling
    try:
        resp=requests.get(url=f'http://ws.audioscrobbler.com/2.0/?method=track.search&track={query}&api_key={key}&format=json&limit=5')
        logger.debug(f"Last.fm API request URL: {resp.url}")
        data=resp.json()
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for {song_name} by {artist_name}: {e}")
        return None
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error for {song_name} by {artist_name}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API error for {song_name} by {artist_name}: {e}")
        return None
    except ConnectionError as e:
        logger.error(f"Connection error for {song_name} by {artist_name}: {e}")
        return None
    
    results = data.get('results', {})
    trackmatches= results.get('trackmatches', {})
    tracks= trackmatches.get('track', [])

    if not tracks:
        logger.warning(f'No tracks found for {song_name} by {artist_name}')
        return None



    best_match=None
    best_score=0
    #iterate through potential matched tracks
    for track in tracks:
        #get metrics and normalize
        song_title=normalize_song_name(track.get("name", None)).lower()
        artist_title=normalize_song_name(track.get('artist', None)).lower()
        listeners=int(track.get('listeners', 0))


        if not song_title or not artist_title or listeners == 0:
            logger.warning(f"Invalid track data for {song_title} by {artist_title}")
            continue

        song_score=similarity_score(song_name_normalized, song_title)
        artist_score= similarity_score(artist_name_normalized, artist_title)

        #Ensuring that the song and artist match closely (doesn't have to be perfect)
        if song_score <.8:
            logger.debug(f"Song score too low: {song_title} by {artist_title} ({song_score:.2f})")
            continue
        if artist_score <.7:
            logger.debug(f"Artist score too low: {song_title} by {artist_title} ({artist_score:.2f})")
            continue
        
       
        original_artist = artist_name.lower().strip()

        #rerun similarity test on artist to perform error handing again
        if similarity_score(original_artist, artist_name)< 0.7:
            logger.warning(f"Artist mismatch: Last.fm '{artist_name}' vs Spotify '{original_artist}'")

        if artist_title in ['unknown', "<unknown>", '']:
            logger.warning(f"Invalid artist name from Last.fm: {artist_title}")
            continue
        if int(listeners) < 10:
            logger.debug(f"Too few listeners: {listeners} for {song_title} by {artist_title}")
            continue

        logger.debug(f"Scores - Song: {song_score:.2f}, Artist: {artist_score:.2f} for {song_title} by {artist_title}")

        #get total score by normalizing the values
        total_score=(song_score*.5) + (artist_score*.5)

        #determine the best match 
        if total_score > best_score:
            best_score = total_score
            best_match = {
                'song_name': song_title,
                'artist_name' : artist_title,
                'listeners': listeners,
                'original_song_name': song_name,
                'original_artist_name': artist_name,
                'artist_id': artist_id,
                'song_id':song_id
            }
        elif total_score == best_score:
            if int(listeners) > int(best_match['listeners']):
                best_match = {
                'song_name': song_title,
                'artist_name' : artist_title,
                'listeners': listeners,
                'original_song_name': song_name,
                'original_artist_name': artist_name,
                'artist_id': artist_id,
                'song_id':song_id
            }
        time.sleep(random.uniform(.5, 1))
            
    # ensure the match is relatively similar
    if best_match and best_score > .8:
        logger.info(f'Best match found: {best_match["song_name"]} by {best_match["artist_name"]} (score: {best_score:.2f})')
        return best_match
    else:
        logger.warning(f"No strong matches found for {song_name} by {artist_name}")
        return None




def match_artists_from_lastfm(track_data, key):
    #get artist_name to verify data is present
    original_artist_name = track_data.get('artist_name', None)
    if not original_artist_name:
        return None
    #call API and error handle
    try:
        resp=requests.get(f'http://ws.audioscrobbler.com/2.0/?method=artist.getInfo&api_key={key}&artist={original_artist_name}&format=json&limit=5')
        resp.raise_for_status()
        data=resp.json()
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for artist {original_artist_name}: {e}")
        return None
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error for artist {original_artist_name}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API error for artist {original_artist_name}: {e}")
        return None
    except ConnectionError as e:
        logger.error(f"Connection error for artist {original_artist_name}: {e}")
        return None

    # Debug: print(json.dumps(data, indent=2))
    
    #Dig through the JSON
    artist= data.get('artist', {})
    stats = artist.get('stats', {})
    if not artist:
        return None
    
    #get name and normalize for similarity score
    artist_name = artist.get('name', None).lower().strip()
    original_artist_name=original_artist_name.lower().strip()
    
    artist_score=similarity_score(artist_name, original_artist_name)

    if artist_score<.9:
        return None
    
    #get other useful data and add to track_data
    track_data['mbid']= artist.get('mbid', None)
    track_data['on_tour'] = artist.get('on_tour', 0)
    track_data['artist_listeners']=int(stats.get('listeners', 0))
    track_data['artist_playcount'] = int(stats.get('playcount',0))
    track_data['source']='Lastfm'

    logger.debug(f"Processed track data: {track_data}")
    return track_data

def process_last_fm_data(song_name, artist_name, song_id, artist_id, key):
    try:

        match_data = get_track_from_lastfm(song_name, artist_name, song_id, artist_id, key)
        if not match_data:
            logger.warning(f"No track data found for: {song_name} by {artist_name}")
            return None


        complete_data = match_artists_from_lastfm(match_data, key)
        if not complete_data:
            logger.warning(f"Artist matching failed for: {song_name} by {artist_name}")
            return None
        return complete_data

    except Exception as e:
        logger.error(f"Error processing {song_name} by {artist_name}: {e}")
        return None

if __name__ == '__main__':
    
    #SETUP
    try:
        load_dotenv()
        key = os.getenv("LAST_FM_KEY")
        conn, cur=get_db()
        producer = create_producer('music-streaming-producer')
        track_error_count =0
        track_success_count=0
        #query database for song and artist names where there is missing lastfm data
        cur.execute('SELECT s.song_name, a.artist_name,s.song_id, s.artist_id FROM songs AS s JOIN artists AS a ON s.artist_id=a.artist_id WHERE s.engagement_ratio IS NULL order by s.created_at desc')
        res=cur.fetchall()
        cpu_count= multiprocessing.cpu_count()
        max_workers = max(8, cpu_count)
        pending_batch = []
        batch_size = 5

        with ProcessPoolExecutor(max_workers=max_workers) as w:
            futures = {w.submit(process_last_fm_data, song_name, artist_name, song_id, artist_id, key):(song_name, artist_name, song_id,artist_id) for song_name, artist_name, song_id, artist_id in res}
        
            for future in as_completed(futures):
                
                song_name, artist_name, song_id, artist_id=futures[future]
                try:
                    data= future.result(timeout=60)
                    logger.debug(f"Processed data: {data}")
                    if data:
                        pending_batch.append(data)
                        if len(pending_batch) >= batch_size:
                            successful, failed = safe_batch_send(pending_batch, 'lastfm_artist', producer, batch_size=batch_size)
                            track_success_count += successful
                            track_error_count += failed
                            logger.info(f'Batch sent: {successful} success, {failed} failed')
                            pending_batch.clear()
                        logger.debug(f'Sent {song_name} through kafka')
                    else:
                        track_error_count+=1
                        continue
                except Exception as e:
                    logger.error(f"Error getting data from Last.fm for {song_name}: {e}")
            
                

        if pending_batch:
            successful, failed = safe_batch_send(pending_batch, 'lastfm_artist', producer, batch_size=batch_size)
            track_success_count += successful
            track_error_count += failed
            logger.info(f'Final batch sent: {successful} success, {failed} failed')


        logger.info(f"Track processing complete - Success: {track_success_count}, Errors: {track_error_count}")
        flush_kafka_producer(producer)
    except Exception as e:
        logger.error(f"Error during Last.fm data extraction: {e}")

    


       
    
        
    

