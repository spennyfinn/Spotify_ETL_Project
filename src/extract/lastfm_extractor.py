from librosa import ex
from pandas.core.config_init import data_manager_doc
import requests
import os
import json
from src.utils.kafka_utils import create_producer, flush_kafka_producer, send_through_kafka
from src.utils.text_utils import normalize_song_name, similarity_score
from src.utils.database import get_db
from dotenv import load_dotenv
import re


def get_track_from_lastfm(song_name, artist_name, song_id,artist_id, key):
    #normalize song and artist names
    #print(f"SONG:{song_name} ARTIST:{artist_name}")
    song_name_normalized= normalize_song_name(song_name)
    artist_name_normalized=normalize_song_name(artist_name)
    #print(f"SONG Norm:{song_name_normalized} ARTIST Norm:{artist_name_normalized}")

    #define url parameters
    query = f"{song_name_normalized} {artist_name_normalized}"
    
    
    #call API with exception handling
    try:
        resp=requests.get(url=f'http://ws.audioscrobbler.com/2.0/?method=track.search&track={query}&api_key={key}&format=json&limit=5')
        resp.raise_for_status()
        data=resp.json()
    except json.JSONDecodeError as e:
        print(f"There was an error when decoding th JSON for {song_name} by {artist_name}: {e}")
        return None
    except requests.exceptions.Timeout as e:
        print(f"There was a timeout error for {song_name} by {artist_name}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"API error for {song_name} by {artist_name}: {e}")
        return None
    except ConnectionError as e:
        print(f"Connection error for {song_name} by {artist_name}: {e}")
        return None

    #parse results
    results = data.get('results', {})
    trackmatches= results.get('trackmatches', {})
    tracks= trackmatches.get('track', [])

    if not tracks:
        print(f'No tracks were found for {song_name} by {artist_name}')
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
            print(f"There was an error retrieving data for {song_title} by {artist_title}")
            continue

        song_score=similarity_score(song_name_normalized, song_title)
        artist_score= similarity_score(artist_name_normalized, artist_title)

        #Ensuring that the song and artist match closelt (doesn't have to be perfect)
        if song_score <.8:
            print(f"Song score was too low to continue: {song_title} by {artist_title} with a score of {song_score:.2f}")
            continue
        if artist_score <.7:
            print(f"Artist score was too low to continue: {song_title} by {artist_title} with a score of {artist_score:.2f}")
            continue
        
        #get the original artist from the db
        original_artist = artist_name.lower().strip()

        #rerun similarity test on artist to perform error handing again
        if similarity_score(original_artist, artist_name)< 0.7:
            print(f"Lastfm artist: {artist_name} doesn't match Spotify artist: {original_artist}")
        
        if artist_title in ['unknown', "<unknown>", '']:
            print(f"The artist name from lastfm is invalid: {artist_title}")
            continue
        if int(listeners) < 10:
            print(f"Too few listeners: {listeners}")
            continue

        print(f"The song score for {song_title} was {song_score:.2f}\nThe artist score for {artist_title} was {artist_score:.2f}")

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
            
    # ensure the match is relatively similar
    if best_match and best_score > .8:
        print(f'Best match {best_match['song_name']} by {best_match['artist_name']} with a score of: {best_score:.2f}')
        return best_match
    else:
        print(f"There weren't strong enough matches for {song_name} by {artist_name}")
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
        print(f"There was an error when decoding the JSON for {original_artist_name}: {e}")
        return None
    except requests.exceptions.Timeout as e:
        print(f"There was a timeout error for {original_artist_name}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"API error for {original_artist_name}: {e}")
        return None
    except ConnectionError as e:
        print(f"Connection error for {original_artist_name} {e}")
        return None
    
    #print(json.dumps(data, indent=2))
    
    #Dig through the JSON
    artist= data.get('artist', {})
    stats = artist.get('stats', {})
    if not artist:
        return None
    
    #get name and normalize for similarity score
    artist_name = artist.get('name', None).lower().strip()
    original_artist_name=original_artist_name.lower().strip()
    
    artist_score=similarity_score(artist_name, original_artist_name)
    #if it is not an exact match return
    if artist_score!=1.0:
        return None
    
    #get other useful data and add to track_data
    track_data['artist_id']=artist_id
    track_data['mbid']= artist.get('mbid', None)
    track_data['url'] = artist.get('url', None)
    track_data['on_tour'] = artist.get('on_tour', 0)
    track_data['artist_listeners']=int(stats.get('listeners', 0))
    track_data['artist_playcount'] = int(stats.get('playcount',0))
    track_data['source']='Lastfm'

    print(track_data)
    print()
    return track_data



if __name__ == '__main__':
    
    #SETUP
    load_dotenv()
    key = os.getenv("LAST_FM_KEY")
    conn, cur=get_db()
    producer = create_producer('music-streaming-producer')

    #query database for song and artist names where there is missing lastfm data
    cur.execute('SELECT s.song_name, a.artist_name,s.song_id, s.artist_id FROM songs AS s JOIN artists AS a ON s.artist_id=a.artist_id WHERE s.engagement_ratio IS NULL')
    res=cur.fetchall()
    
    #success/error counters
    track_error_count =0
    track_success_count=0
    for song_name, artist_name,song_id, artist_id in res:
        #get the track data from last fm
        match_data =get_track_from_lastfm(song_name, artist_name,song_id,artist_id, key)
        if not match_data:
            track_error_count+=1
            continue
        #if successful get the artist data and send through kafka
        track_success_count+=1
        complete_data=match_artists_from_lastfm(match_data, key)
        if complete_data:
            send_through_kafka(complete_data, 'lastfm_artist', producer)

    print(f"Track Success count: {track_success_count}")
    print(f"Track Error count: {track_error_count}")
    flush_kafka_producer(producer)

    


       
    
        
    

