import requests
from dotenv import load_dotenv
import os

from src.extract.lastfm_extractor import send_through_kafka
import time
import base64
import json
from confluent_kafka import Producer
from urllib.parse import quote
from src.utils.kafka_utils import create_producer
from src.utils.text_utils import normalize_song_name, similarity_score, has_collaborators, extract_collaborators
from src.utils.spotify_utils import get_spotify_token
from src.utils.database import get_db, get_song_needing_spotify_data
# -------------------------------
# Environment Configuration
# -------------------------------
load_dotenv()
CLIENT_ID=os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET=os.getenv('SPOTIFY_CLIENT_SECRET')

logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )




# -------------------------------
# SQL QUERY
# -------------------------------






def search_track(song_artist, access_token):
    """
    Search for a track on Spotify and find the best matching result.
    
    Handles remixes and collaborations by matching based on whether the original
    song has collaborators. If original has no collaborators, prefers simple versions.
    If original has collaborators, only matches songs with matching collaborators.
    
    Args:
        song_artist (tuple): Tuple containing (song_name, artist_name)
        access_token (str): Spotify API access token
        
    Returns:
        dict: Track data dictionary if match found, None otherwise
    """
    headers={
         'Authorization': f'Bearer {access_token}'
    }
    original_song, original_artist = song_artist
    print(f"Searching for: '{original_song}' by {original_artist}")
    
    song = quote(original_song)
    artist = quote(original_artist)
    
    try:
        search_url=f'https://api.spotify.com/v1/search?q=track:{song}+artist:{artist}&type=track&limit=20'
        response=requests.get(search_url, headers=headers)
        response.raise_for_status()
        resp=response.json()
    except requests.ConnectionError as e:
        print(f"There was a connection error for {original_song} by {original_artist}: {e}")
        return None
    except requests.RequestException as e:
        print(f"HTTP request failed for {original_song} by {original_artist}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response for {original_song} by {original_artist}: {e}")
        return None
    
    try:
        tracks=resp.get('tracks', None)
        if not tracks:
            print(f"No tracks object in response for {original_song} by {original_artist}")
            return None
        items=tracks.get('items',[])
        if not items or len(items) == 0:
            print(f"No items in response for {original_song} by {original_artist}")
            return None

        normalized_original_base = normalize_song_name(original_song)
        normalized_original_artist = original_artist.lower().strip()
        original_has_collabs = has_collaborators(original_song)
        original_collaborators = extract_collaborators(original_song)
        
        best_match = None
        best_score = 0
        
        for item in items:
            spotify_song_name = item.get('name', '')
            spotify_artists = item.get('artists', [])
            
            if not spotify_artists:
                continue
                
            spotify_artist_name = spotify_artists[0].get('name', '').lower().strip()
            spotify_has_collabs = has_collaborators(spotify_song_name)
            normalized_spotify_base = normalize_song_name(spotify_song_name)
            
            song_similarity = similarity_score(normalized_original_base, normalized_spotify_base)
            artist_similarity = similarity_score(normalized_original_artist, spotify_artist_name)
            exact_base_match = normalized_original_base == normalized_spotify_base
            
            if not original_has_collabs and spotify_has_collabs:
                if not exact_base_match:
                    continue
                song_similarity *= 0.3
            
            elif original_has_collabs:
                spotify_collaborators = extract_collaborators(spotify_song_name)
                if spotify_collaborators and original_collaborators:
                    original_collabs_normalized = [c.lower().strip() for c in original_collaborators]
                    spotify_collabs_normalized = [c.lower().strip() for c in spotify_collaborators]
                    collab_match = any(
                        any(orig_collab in spot_collab or spot_collab in orig_collab 
                            for orig_collab in original_collabs_normalized)
                        for spot_collab in spotify_collabs_normalized
                    )
                    if not collab_match:
                        continue
                elif not spotify_collaborators and original_collaborators:
                    continue
            
            combined_score = (song_similarity * 0.7) + (artist_similarity * 0.3)
            
            if exact_base_match:
                combined_score = min(1.0, combined_score + 0.2)
            
            if (exact_base_match and 
                normalized_original_artist == spotify_artist_name and
                original_has_collabs == spotify_has_collabs):
                combined_score = 1.0
            
            if combined_score > best_score:
                best_score = combined_score
                best_match = item
        
        if not best_match or best_score < 0.5:
            print(f"✗ No good match found for '{original_song}' by {original_artist} (best score: {best_score:.2f})")
            return None
        
        matched_song = best_match.get('name', '')
        matched_artist = best_match.get('artists', [{}])[0].get('name', 'Unknown')
        print(f"✓ Found match: '{matched_song}' by {matched_artist} (score: {best_score:.2f})")
        
        item = best_match
        albums_data=item.get('album',None)
        artist_datas=item.get('artists', None)

        if not albums_data or not artist_datas or len(artist_datas) == 0:
            print(f"Missing required data for {original_song} by {original_artist}")
            return None

        artist_data=artist_datas[0]
        data={
        'album_type':albums_data.get('album_type', None),
        'is_playable':item.get('is_playable', None), 
        'album_name': albums_data.get('name', None),
        'album_id': albums_data.get('id', None),
        'name':item.get('name', None),
        'artist_name': artist_data.get('name', None),
        'artist_id': artist_data.get('id', None),
        'release_date': albums_data.get('release_date', None),
        'release_date_precision':albums_data.get('release_date_precision', None),
        'album_total_tracks': albums_data.get('total_tracks', None),
        'type': item.get('type', None),
        'explicit':item.get('explicit', None),
        'popularity': item.get('popularity', None),
        'track_number':item.get('track_number',None),
        'duration_ms': item.get('duration_ms', None),
        'song_id': item.get('id',None),
        'source': 'Spotify'}
    except (IndexError, TypeError, KeyError) as e:
        print(f"Error parsing response for {original_song} by {original_artist}: {e}")
        return None
    time.sleep(.5)
    return data


if __name__=='__main__':
    import logging
    
    producer = create_producer('music-streaming-producer')
    
    check_interval = 3600  # Check for new songs every hour
    
    logging.info("Starting continuous Spotify extract process")
    logging.info(f"Will check for songs needing Spotify data every {check_interval/3600} hour")
    
    while True:
        conn = None
        cur = None
        try:
            conn, cur = get_db()
            access_token=get_spotify_token()

            if not access_token:
                logging.error("Failed to get Spotify access token")
                time.sleep(60)
                continue

            song_artist_list = get_song_needing_spotify_data(cur)
            
            if not song_artist_list:
                logging.info("No songs need Spotify data at this time")
            else:
                logging.info(f"Found {len(song_artist_list)} songs needing Spotify data")
                success_count=0
                failure_count=0

                for i in song_artist_list:
                    data=search_track(i, access_token)
                    if data:
                        logging.info(f"Successfully extracted data for {data['name']} by {data['artist_name']}")
                        success_count+=1
                        send_through_kafka(data)
                    else:
                        logging.warning(f"Failed to extract data for {i[0]} by {i[1]}")
                        failure_count+=1
                
                logging.info(f"Batch complete. Success: {success_count}, Failed: {failure_count}")
            
            if conn and cur:
                cur.close()
                conn.close()
            
            logging.info(f"Waiting {check_interval/3600} hour until next check...")
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            logging.info("Shutting down Spotify extract process...")
            if conn and cur:
                cur.close()
                conn.close()
            break
        except Exception as e:
            logging.error(f"Error in Spotify extract: {e}")
            if conn and cur:
                cur.close()
                conn.close()
            logging.info("Retrying in 60 seconds...")
            time.sleep(60)







