import base64
import os
import json
import requests
import time
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)








lastfm_song_query = ("INSERT INTO songs(song_name,song_id, song_listeners, artist_id,mbid,engagement_ratio) "
                 "VALUES (%s, %s, %s, %s, %s, %s) "
                 "ON CONFLICT (song_id) DO UPDATE SET "
                 "song_listeners = EXCLUDED.song_listeners, "
                 "engagement_ratio = EXCLUDED.engagement_ratio, "
                 "mbid = EXCLUDED.mbid, "
                 "updated_at = CURRENT_TIMESTAMP; ")
                 
lastfm_artist_query = ("INSERT INTO artists(artist_name,artist_id, on_tour, total_listeners, total_playcount, plays_per_listener) "
            "VALUES (%s,%s, %s, %s, %s, %s) "
            "ON CONFLICT (artist_id) DO UPDATE "
            "SET on_tour = EXCLUDED.on_tour, "
            "total_listeners = EXCLUDED.total_listeners,"
            "total_playcount = EXCLUDED.total_playcount,"
            "plays_per_listener=EXCLUDED.plays_per_listener, "
            "updated_at = CURRENT_TIMESTAMP; ")


spotify_song_query=('INSERT INTO songs(song_name, artist_id, duration_ms, duration_seconds, duration_minutes, release_date, release_date_precision, is_explicit, popularity, track_number, song_id, album_id, is_playable) '
                   'VALUES(%s,%s,%s ,%s,%s,%s,%s,%s,%s,%s, %s, %s, %s) ' \
                   'ON CONFLICT (song_id) '
                   'DO UPDATE ' \
                    'SET duration_seconds = EXCLUDED.duration_seconds,' \
                    'duration_minutes = EXCLUDED.duration_minutes,' \
                    'duration_ms= EXCLUDED.duration_ms,' \
                    'release_date = EXCLUDED.release_date,' \
                    'release_date_precision=EXCLUDED.release_date_precision,' \
                    'is_explicit=EXCLUDED.is_explicit,' \
                    'popularity= EXCLUDED.popularity,' \
                    'track_number= EXCLUDED.track_number,' \
                    'is_playable = EXCLUDED.is_playable, '
                    'album_id = EXCLUDED.album_id, '
                    'updated_at = CURRENT_TIMESTAMP; '
                   )
spotify_album_query=('INSERT INTO albums(album_title, artist_id,album_type, album_total_tracks, album_id) '
                    'VALUES(%s,%s,%s,%s, %s) '
                    'ON CONFLICT (album_id) DO UPDATE '
                    'SET album_type = EXCLUDED.album_type,'
                    'album_total_tracks = EXCLUDED.album_total_tracks, '
                    'updated_at = CURRENT_TIMESTAMP;')

spotify_artist_query= ('INSERT INTO artists (artist_id, artist_name) '
                        'VALUES(%s,%s) '
                        'ON CONFLICT (artist_id) DO UPDATE SET '
                        'artist_name = EXCLUDED.artist_name, '
                        'updated_at = CURRENT_TIMESTAMP; '
                        )



insert_audio_features_query= ('INSERT INTO song_audio_features(song_id, bpm, energy, spectral_centroid, zero_crossing_rate, danceability, preview_url, harmonic_ratio, percussive_ratio) '
                              'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) '
                              'ON CONFLICT (song_id) DO UPDATE SET '
                              'bpm = EXCLUDED.bpm, '
                              'energy = EXCLUDED.energy, '
                              'spectral_centroid = EXCLUDED.spectral_centroid, '
                              'zero_crossing_rate = EXCLUDED.zero_crossing_rate, '
                              'danceability = EXCLUDED.danceability, '
                              'preview_url = EXCLUDED.preview_url, '
                              'harmonic_ratio = EXCLUDED.harmonic_ratio, '
                              'percussive_ratio = EXCLUDED.percussive_ratio;'
)

insert_artist_data_query = ('INSERT INTO artists(artist_id, artist_popularity, artist_followers, artist_name, has_genres) '
                            'VALUES (%s, %s, %s, %s, %s) '
                            'ON CONFLICT (artist_id) DO UPDATE SET '
                            'artist_popularity = EXCLUDED.artist_popularity, '
                            'artist_followers = EXCLUDED.artist_followers, '
                            'artist_name = EXCLUDED.artist_name, '
                            'has_genres = EXCLUDED.has_genres;'
                            )

insert_genres_query=('INSERT INTO genres(genre_name) '
                    'VALUES (%s) '
                    'ON CONFLICT (genre_name) DO NOTHING;')




# -------------------------------
# TOKEN FUNCTIONS
# -------------------------------
def get_spotify_token():
    """
    Get Spotify access token, loading from file if valid or requesting new one.
    
    Returns:
        str: Access token if successful, None otherwise
    """
    
    token = load_token()
    if token:
        return token
    load_dotenv()
    auth_str = f"{os.getenv('SPOTIFY_CLIENT_ID')}:{os.getenv('SPOTIFY_CLIENT_SECRET')}"
    b64_auth = base64.b64encode(auth_str.encode()).decode("utf-8")

    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "client_credentials"
    }

    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    
    if response.status_code != 200:
        logger.error("Token request failed - STATUS: %s, BODY: %s", response.status_code, response.text)
        return None

    resp=response.json()
    access_token= resp.get('access_token')
    expires_in=resp.get('expires_in')
    if not expires_in:
        logger.warning("No expires_in in token response")
        return None
    save_token(access_token,expires_in)
    return access_token


def save_token(token, expires_in):
    """
    Save Spotify access token to file with expiration time.
    
    Args:
        token (str): Access token to save
        expires_in (int): Seconds until token expires
    """
    if not token or not expires_in:
        raise ValueError("Token and expires_in are required")
    data={
         'token': token,
         'expires_at': time.time() + expires_in -5
    }

    with open( "spotify_token.json", 'w') as f:
         json.dump(data,f)


def load_token():
    """
    Load Spotify access token from file if it exists and isn't expired.
    
    Returns:
        str: Access token if valid, None otherwise
    """
    try:
        with open('spotify_token.json', 'r') as f:
            data=json.load(f)
        if time.time() < data['expires_at']:
            return data['token']
    except FileNotFoundError:
        return None
    return None

def extract_spotify_data(data):
        data_list=[]

        tracks = data.get('tracks', {})
        items= tracks.get('items', [])
        for item in items:
            albums_data=item.get('album',None)
            artist_data=item.get('artists', None)

            if not artist_data or not albums_data:
                logger.warning(f"Missing data for track '{item.get('name', 'Unknown')}', skipping")
                continue

            try:
                artist_data=artist_data[0]
            except IndexError as e:
                logger.warning("No artist data found for track")
                continue


            track_data={
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
            data_list.append(track_data)
        return data_list




    
    
    

