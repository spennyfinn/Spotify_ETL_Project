import pytest


@pytest.fixture
def data():
    return{
        'song_name': 'Test Song',
        'artist_id': '1234567890123456789012',
        'song_id': '1gj856fdB53pL96DStrn08',
        'bpm': 60.2,
        'energy': .93,
        'spectral_centroid': 500.2,
        'zero_crossing_rate': 0.5,
        'danceability': .6553,
        'preview_url': 'https://audio_features.com',
        'harmonic_ratio': .5,
        'percussive_ratio': .5,
        'source': 'preview_url'
    }

@pytest.fixture
def valid_spotify_data()-> dict:
    return{
        'album_type': 'album',
        'is_playable': True,
        'album_id': '1234567890abcdefghijk1',
        'song_name': 'Test Song ',
        'artist_name': 'Test Artist',
        'release_date': '2023-01-01',
        'release_date_precision': 'day',
        'album_total_tracks': 10,
        'track_number':1,
        'is_explicit': True,
        'popularity': 70,
        'song_id': '1io456789012aer6789012',
        'duration_ms': 200000,
        'duration_seconds' : 200,
        'duration_minutes' : 3.33,
        'artist_id' : 'wer45poiup1234567nnpp2',
        'album_title': 'Test Album'
        }

@pytest.fixture
def lastfm_data():
    return{
        'song_name': 'Test Song ',
        'artist_name': 'Test Artist',
        'num_song_listeners': 50000,
        'song_url': 'https://song_url.com',
        'mbid': '12345678-abc3-4d4c-0b90-0987654321ab',
        'on_tour': False,
        'song_id': '21lop6789fyt385Yt890ab',
        'artist_total_playcount': 100000,
        'artist_total_listeners': 200000,
        'plays_per_listener': .5,
        'engagement_ratio':.25,
        'artist_id': '1Er4567890BOutf6789012'
        }

# ############################
# PARSER FIXTURES
##############################
@pytest.fixture()
def valid_lastfm_data():
    return {
        'song_name': 'test song',
        'artist_name': 'test artist',
        'artist_id': '1234567890123456789012',
        'num_song_listeners': 10000,
        'mbid': '12345678-1234-1234-1234-123456789012',
        'song_url': 'https://url.com',
        'on_tour': False,
        'artist_total_listeners': 80000,
        'artist_total_playcount': 900000,
        'song_id': '123456789008765432112',
        'engagement_ratio': .7,
        'plays_per_listener': .3,
        'source': 'Lastfm'
    }

@pytest.fixture
def valid_audio_features():
        return {
            'song_name': 'test_song',
            'artist_id': '1234567890123456789012',
            'bpm': 100.0,
            'energy': .5,
            'zero_crossing_rate': .17,
            'spectral_centroid': 1000.0,
            'danceability': .7,
            'preview_url': 'https://test.com',
            'harmonic_ratio': .51,
            'percussive_ratio': .49,
            'source': 'preview_url'
        }

@pytest.fixture
def valid_spotify_data()-> dict:
        '''Returns an instance of valid spotify data'''
        return {
            'song_name': 'test song',
            'artist_name': 'test artist',
            'artist_id': '1234567890123456789012',
            'popularity': 99,
            'album_title': 'test album',
            'album_id': '1029384756019283746501',
            'album_type': 'single',
            'is_playable': True,
            'release_date': '2023-02-02',
            'release_date_precision': 'day',
            'album_total_tracks': 16,
            'track_number': 3,
            'is_explicit': True,
            'duration_ms': 600000,
            'duration_seconds': 600,
            'duration_minutes': 100,
            'song_id': 'p0o9i8u7y6t5r4e3w2q112',
            'source':'Spotify'
        }    