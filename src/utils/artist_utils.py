import json
import uuid
import os


def get_artist_id(artist_name, artist_id, artist_id_dict, filepath):
     """
    Retrieve or generate a unique ID for an artist.

    Args:
        artist_name (str): Name of the artist.
        artist_id (str): Existing artist ID, if available.
        artist_id_dict (dict): Dictionary mapping artist names to unique IDs.
        id_dict_path (str): Path to JSON file storing artist IDs.

    Returns:
        str: Unique artist ID (existing or newly generated UUID).
    """
     key =artist_name.strip().lower()
     if artist_id and artist_id!='N/A':
          return artist_id
     if key in artist_id_dict:
          return artist_id_dict[key]
     new_id = str(uuid.uuid4())
     artist_id_dict[key]=new_id
     save_artist_ids(artist_id_dict, filepath)
     return new_id

def save_artist_ids(artist_id_dict: dict[str:str], filepath= 'artists_ids.json'):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(artist_id_dict, 'w') as f:
          json.dump(artist_id_dict, f,indent=4)

def load_artist_ids(filepath: str = 'artists_ids.json'):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

     