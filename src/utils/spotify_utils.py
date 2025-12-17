import base64
import os
import json
import requests
import time
from dotenv import load_dotenv


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
        print("STATUS:", response.status_code)
        print("BODY:", response.text)
        return None

    resp=response.json()
    access_token= resp.get('access_token')
    expires_in=resp.get('expires_in')
    if not expires_in:
        print("No expires_in in response")
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
                print(f"There is missing data for {item.get('name', 'Unknown')}, skipping")
                continue

            try:
                artist_data=artist_data[0]
            except IndexError as e:
                print("There is no artist data")
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


def get_song_and_artist_name(data):
    song_artist_list=[]
    tracks = data.get('tracks', {})
    items= tracks.get('items', [])
    for item in items:
        albums_data=item.get('album',None)
        artist_data=item.get('artists', None)
        if not artist_data or not albums_data:
            print(f"There is missing data for {item.get('name', 'Unknown')}, skipping")
            continue
        try:
            artist_data=artist_data[0]
        except IndexError as e:
            print("There is no artist data")
            continue
    
        song_name=item.get('name', None)
        artist_name=artist_data.get('name', None)
        if not song_name or not artist_name:
            print(f"Missing either song name or artist name")
            continue
        song_artist_list.append((song_name, artist_name))
    return song_artist_list