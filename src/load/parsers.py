import uuid




def parse_lastfm_message(data):
    song=[
        data['song_name'],
        data['song_id'],
        data['num_song_listeners'],
        data['artist_id'],
        data['song_url'], 
        data['mbid'],
        data['engagement_ratio'],
        ]
    print(song)
    artist=[
        data['artist_name'],
        data['artist_id'],
        data['on_tour'],
        data['artist_total_listeners'],
        data['artist_total_playcount'],
        data['plays_per_listener']

        ]
    return song,artist





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
        data['song_id'],
        data['album_id']
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

