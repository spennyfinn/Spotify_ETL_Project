import uuid




def parse_insert_message(data):
        """
    Parse a transformed track message into rows for different database tables.

    Args:
        data (dict): Transformed music track data

    Returns:
        Tuple containing:
            song_row (list)
            artist_row (list)
            album_row (list)
            tag_rows (list of lists)
            similar_artist_rows (list of lists)
    """
       
        song_row=[
            data['song_name'],
            data['song_id'],
            data['num_song_listeners'],
            "",
            data['artist_id'],
            data['song_url'],
            data['engagement_ratio']
        ]

        artist_row=[
            data['artist_id'],
            data['artist_name'] ,
            data['artist_url'],
            data['on_tour'] ,
            data['artist_total_listeners'] ,
            data['artist_total_playcount'] ,
            data['plays_per_listener'] 
        ]

        album_row=[
            str(uuid.uuid4()),
            data['album_title'],
            data['artist_name']
        ]


        tag_rows = [[data['song_name'], data['artist_id'], tag] for tag in data['tags']]
        
        similar_artist_rows = [[data['artist_name'], sim] for sim in data['similar_artists']]

        return song_row, artist_row, album_row, tag_rows, similar_artist_rows

def parse_spotify_message(data):
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
        data['song_id']
    ]
    album=[
        data['album_title'],
        data['artist_name'],
        data['album_type'],
        data['album_total_tracks'],
        data['album_id']]
    
    artist = [
        data['artist_id'],
        data['artist_name']
    
    ]

    return song, album, artist


def parse_audio_features_data(data):
    audio_features=[
        data['song_name'],
        data['artist_id'],
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

