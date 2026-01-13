




import logging

logger = logging.getLogger(__name__)

def parse_lastfm_message(data):
    logger.debug(f'Parsing Last.fm message: {data}')
    if type(data) is not dict:
        raise TypeError(f'The input data should be a dictionary but it was {type(data)}')

    required_fields = ['song_name', 'artist_id', 'artist_name']
    missing = [field for field in required_fields if field not in data or data[field] is None]
    if missing:
        raise ValueError(f'These required fields are missing from the data {', '.join(missing)}')
    try: 
        song=[
            data['song_name'],
            data['song_id'],
            data['num_song_listeners'],
            data['artist_id'],
            data['mbid'],
            data['engagement_ratio'],
            ]

        artist=[
            data['artist_name'],
            data['artist_id'],
            data['on_tour'],
            data['artist_total_listeners'],
            data['artist_total_playcount'],
            data['plays_per_listener']
            ]
        return song,artist

    except (TypeError, ValueError,KeyError) as e:
        raise ValueError(f"There is invalid data in the input data: {str(e)}")
    





def parse_spotify_message(data):
    if type(data) is not dict:
        raise TypeError(f"Input data should be a dictionary but it is: {type(data)}")
    
    required_fields = ['song_name', 'artist_name', 'duration_ms', 'popularity', 'song_id', 'artist_id', 'album_id']
    missing = [field for field in  required_fields if field not in data or data[field] is None]
    if missing:
        raise ValueError(f"There is at least one missing required field: {', '.join(missing)}")

    try:
        song=[
            data['song_name'],
            data['artist_id'],
            data['duration_ms'],
            data['duration_seconds'],
            data['duration_minutes'],
            data['release_date'],
            data['release_date_precision'],
            data['is_explicit'],
            data['popularity'],
            data['track_number'],
            data['song_id'],
            data['album_id'],
            data['is_playable']
        ]
        album=[
            data['album_title'],
            data['artist_id'],
            data['album_type'],
            data['album_total_tracks'],
            data['album_id']
            ]

        artist = [
            data['artist_id'],
            data['artist_name']

        ]
        logger.debug(f'Parsed artist data: {artist}')
        return song, album, artist

    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f'There was invalid data: {str(e)}')


def parse_audio_features_data(data):
    if type(data) is not dict:
        raise TypeError(f"Input data should be a dict but it was: {type(data)}")

    required_fields =  ['song_id', 'bpm', 'energy', 'spectral_centroid', 'zero_crossing_rate', 'danceability', 'preview_url', 'harmonic_ratio', 'percussive_ratio']
    missing = [field for field in required_fields if field not in data or data[field] is None]
    if missing:
        raise ValueError(f"There is at least one missing required field: {', '.join(missing)}")

    try:
        audio_features=[
            data['song_id'],
            data['bpm'],
            data['energy'],
            data['spectral_centroid'],
            data['zero_crossing_rate'],
            data['danceability'],
            data['preview_url'],
            data['harmonic_ratio'],
            data['percussive_ratio']
        ]
        return audio_features
        
    except (TypeError, ValueError, KeyError) as e:
        raise ValueError(f"There was invalid or missing data: {str(e)}")

