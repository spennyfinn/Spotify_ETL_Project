import base64
import os
import json
import requests
import time

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
    
    auth_str = f"{os.getenv('CLIENT_ID')}:{os.getenv('CLIENT_SECRET')}"
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
