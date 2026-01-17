import io
import struct
import wave
import math
import numpy as np
import pytest
import responses
from unittest.mock import MagicMock, patch

################################
# SPOTIFY TRACK FIXTURES
################################

@pytest.fixture
def mock_spotify_token():
    with patch('src.extract.spotify_track_extractor.get_spotify_token', return_value = 'fake_token'), \
         patch('src.extract.spotify_artist_extractor.get_spotify_token', return_value = 'fake_token'):
        yield

@pytest.fixture
def mock_database_connection():
    with patch('src.utils.database_utils.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value= (mock_conn, mock_cur)
        yield mock_cur

### Spotify extraction fixtures

@pytest.fixture
def expected_spotify_data_extracted():
    return {
        'as it was':{
            'album_type': 'album',
            'is_playable': None,
            'album_name': 'Harrys House',
            'album_id': '5r36AJ6VOJot3ika5YF74k',
            'name': 'As It Was',
            'artist_name': 'Harry Styles',
            'artist_id': '6KImCVD70vtIoJWnq6nGn3',
            'release_date': '2022-05-20',
            'release_date_precision': 'day',
            'album_total_tracks': 13,
            'type': 'track',
            'explicit': False,
            'popularity': 92,
            'track_number': 4,
            'duration_ms': 167303,
            'song_id': '4Dvkj6JhhA12EX05fT7y2e',
            'source': 'Spotify'
        },
        'heat waves':{
            'album_type': 'album',
            'is_playable': None,
            'album_name': 'Dreamland',
            'album_id': '4yRXW9BV5RW5R7nKP9fXAW',
            'name': 'Heat Waves',
            'artist_name': 'Glass Animals',
            'artist_id': '4yvcSjfu4PC0CYQyLy4wSq',
            'release_date': '2020-08-07',
            'release_date_precision': 'day',
            'album_total_tracks': 16,
            'type': 'track',
            'explicit': False,
            'popularity': 88,
            'track_number': 1,
            'duration_ms': 238805,
            'song_id': '0VjIjW4GlUZAMYd2vXMi3b',
            'source': 'Spotify'
        },
        'stay':{
            'album_type': 'single',
            'is_playable': None,
            'album_name': 'Stay',
            'album_id': '4yRXW9BV5RW5R7nKP9fXBW',
            'name': 'Stay',
            'artist_name': 'The Kid Laroi',
            'artist_id': '2tIP7SsRs7vjIcLrU85W8J',
            'release_date': '2021-07-09',
            'release_date_precision': 'day',
            'album_total_tracks': 1,
            'type': 'track',
            'explicit': True,
            'popularity': 85,
            'track_number': 1,
            'duration_ms': 141805,
            'song_id': '5PjdY0CKGZdEuoNab3yDmX',
            'source': 'Spotify'
        },
        'levitating':{
            'album_type': 'album',
            'is_playable': None,
            'album_name': 'Future Nostalgia',
            'album_id': '7fJJK56U9fHixgO0HBwXmO',
            'name': 'Levitating',
            'artist_name': 'Dua Lipa',
            'artist_id': '6M2wZ9GZgrQXHCFfjv46we',
            'release_date': '2020-03-27',
            'release_date_precision': 'day',
            'album_total_tracks': 11,
            'type': 'track',
            'explicit': False,
            'popularity': 87,
            'track_number': 5,
            'duration_ms': 183274,
            'song_id': '5nujrmhLynf4yMoMtj8AQF',
            'source': 'Spotify'
        }
    }


@pytest.fixture
def expected_transformed_spotify_data():
    return {
        'as it was': {
            'song_name': 'as it was',
            'artist_name': 'harry styles',
            'artist_id': '6KImCVD70vtIoJWnq6nGn3',
            'popularity': 92,
            'album_title': 'harrys house',
            'album_id': '5r36AJ6VOJot3ika5YF74k',
            'album_type': 'album',
            'is_playable': False,
            'release_date': '2022-05-20',
            'release_date_precision': 'day',
            'album_total_tracks': 13,
            'track_number': 4,
            'is_explicit': False,
            'duration_ms': 167303,
            'duration_seconds': 167,
            'duration_minutes': 2.78,
            'song_id': '4Dvkj6JhhA12EX05fT7y2e',
            'source': 'Spotify'
        },
        'heat waves': {
            'song_name': 'heat waves',
            'artist_name': 'glass animals',
            'artist_id': '4yvcSjfu4PC0CYQyLy4wSq',
            'popularity': 88,
            'album_title': 'dreamland',
            'album_id': '4yRXW9BV5RW5R7nKP9fXAW',
            'album_type': 'album',
            'is_playable': False,
            'release_date': '2020-08-07',
            'release_date_precision': 'day',
            'album_total_tracks': 16,
            'track_number': 1,
            'is_explicit': False,
            'duration_ms': 238805,
            'duration_seconds': 238,
            'duration_minutes': 3.97,
            'song_id': '0VjIjW4GlUZAMYd2vXMi3b',
            'source': 'Spotify'
        },
        'stay': {
            'song_name': 'stay',
            'artist_name': 'the kid laroi',
            'artist_id': '2tIP7SsRs7vjIcLrU85W8J',
            'popularity': 85,
            'album_title': 'stay',
            'album_id': '4yRXW9BV5RW5R7nKP9fXBW',
            'album_type': 'single',
            'is_playable': False,
            'release_date': '2021-07-09',
            'release_date_precision': 'day',
            'album_total_tracks': 1,
            'track_number': 1,
            'is_explicit': True,
            'duration_ms': 141805,
            'duration_seconds': 141,
            'duration_minutes': 2.35,
            'song_id': '5PjdY0CKGZdEuoNab3yDmX',
            'source': 'Spotify'
        },
        'levitating': {
            'song_name': 'levitating',
            'artist_name': 'dua lipa',
            'artist_id': '6M2wZ9GZgrQXHCFfjv46we',
            'popularity': 87,
            'album_title': 'future nostalgia',
            'album_id': '7fJJK56U9fHixgO0HBwXmO',
            'album_type': 'album',
            'is_playable': False,
            'release_date': '2020-03-27',
            'release_date_precision': 'day',
            'album_total_tracks': 11,
            'track_number': 5,
            'is_explicit': False,
            'duration_ms': 183274,
            'duration_seconds': 183,
            'duration_minutes': 3.05,
            'song_id': '5nujrmhLynf4yMoMtj8AQF',
            'source': 'Spotify'
        }
    }


@pytest.fixture
def invalid_spotify_transformed_track(expected_transformed_spotify_data):
    track = expected_transformed_spotify_data['as it was'].copy()
    track.pop('artist_id', None)
    return track


@pytest.fixture
def nullified_spotify_transformed_track(expected_transformed_spotify_data):
    track = expected_transformed_spotify_data['as it was'].copy()
    track['song_id'] = None
    return track




@pytest.fixture
def mock_spotify_track_api():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as resp:
        resp.add(
            responses.GET,
            'https://api.spotify.com/v1/search?q=pop&type=track&limit=50&offset=0',
            json={
                'tracks': {
                    'href': 'https://api.spotify.com/v1/search?q=pop&type=track&limit=50&offset=0',
                    'items': [
                        {
                            'album': {
                                'album_type': 'album',
                                'artists': [{'name': 'Harry Styles', 'id': '6KImCVD70vtIoJWnq6nGn3'}],
                                'name': 'Harrys House',
                                'id': '5r36AJ6VOJot3ika5YF74k',
                                'release_date': '2022-05-20',
                                'release_date_precision': 'day',
                                'total_tracks': 13
                            },
                            'artists': [{'name': 'Harry Styles', 'id': '6KImCVD70vtIoJWnq6nGn3'}],
                            'duration_ms': 167303,
                            'explicit': False,
                            'id': '4Dvkj6JhhA12EX05fT7y2e',
                            'name': 'As It Was',
                            'popularity': 92,
                            'track_number': 4,
                            'type': 'track'
                        }
                    ],
                    'limit': 50,
                    'next': 'https://api.spotify.com/v1/search?q=pop&type=track&limit=50&offset=50',
                    'offset': 0,
                    'previous': None,
                    'total': 150
                }
            },
            status=200
        )

        resp.add(
            responses.GET,
            'https://api.spotify.com/v1/search?q=pop&type=track&limit=50&offset=50',
            json={
                'tracks': {
                    'href': 'https://api.spotify.com/v1/search?q=pop&type=track&limit=50&offset=50',
                    'items': [
                        {
                            'album': {
                                'album_type': 'album',
                                'artists': [{'name': 'Glass Animals', 'id': '4yvcSjfu4PC0CYQyLy4wSq'}],
                                'name': 'Dreamland',
                                'id': '4yRXW9BV5RW5R7nKP9fXAW',
                                'release_date': '2020-08-07',
                                'release_date_precision': 'day',
                                'total_tracks': 16
                            },
                            'artists': [{'name': 'Glass Animals', 'id': '4yvcSjfu4PC0CYQyLy4wSq'}],
                            'duration_ms': 238805,
                            'explicit': False,
                            'id': '0VjIjW4GlUZAMYd2vXMi3b',
                            'name': 'Heat Waves',
                            'popularity': 88,
                            'track_number': 1,
                            'type': 'track'
                        }
                    ],
                    'limit': 50,
                    'next': 'https://api.spotify.com/v1/search?q=pop&type=track&limit=50&offset=100',
                    'offset': 50,
                    'previous': 'https://api.spotify.com/v1/search?q=pop&type=track&limit=50&offset=0',
                    'total': 150
                }
            },
            status=200
        )


        resp.add(
            responses.GET,
            'https://api.spotify.com/v1/search?q=pop&type=track&limit=50&offset=100',
            json={
                'tracks': {
                    'href': 'https://api.spotify.com/v1/search?q=pop&type=track&limit=50&offset=100',
                    'items': [
                        {
                            'album': {
                                'album_type': 'single',
                                'artists': [{'name': 'The Kid Laroi', 'id': '2tIP7SsRs7vjIcLrU85W8J'}, {'name': 'Justin Bieber', 'id': '1uNFoZAHBGtllmzznpCI3s'}],
                                'name': 'Stay',
                                'id': '4yRXW9BV5RW5R7nKP9fXBW',
                                'release_date': '2021-07-09',
                                'release_date_precision': 'day',
                                'total_tracks': 1
                            },
                            'artists': [{'name': 'The Kid Laroi', 'id': '2tIP7SsRs7vjIcLrU85W8J'}, {'name': 'Justin Bieber', 'id': '1uNFoZAHBGtllmzznpCI3s'}],
                            'duration_ms': 141805,
                            'explicit': True,
                            'id': '5PjdY0CKGZdEuoNab3yDmX',
                            'name': 'Stay',
                            'popularity': 85,
                            'track_number': 1,
                            'type': 'track'
                        }
                    ],
                    'limit': 50,
                    'next': 'https://api.spotify.com/v1/search?q=pop&type=track&limit=50&offset=150',
                    'offset': 100,
                    'previous': 'https://api.spotify.com/v1/search?q=pop&type=track&limit=50&offset=50',
                    'total': 200
                }
            },
            status=200
        )

        resp.add(
            responses.GET,
            'https://api.spotify.com/v1/search?q=pop&type=track&limit=50&offset=150',
            json={
                'tracks': {
                    'href': 'https://api.spotify.com/v1/search?q=pop&type=track&limit=50&offset=150',
                    'items': [
                        {
                            'album': {
                                'album_type': 'album',
                                'artists': [{'name': 'Dua Lipa', 'id': '6M2wZ9GZgrQXHCFfjv46we'}],
                                'name': 'Future Nostalgia',
                                'id': '7fJJK56U9fHixgO0HBwXmO',
                                'release_date': '2020-03-27',
                                'release_date_precision': 'day',
                                'total_tracks': 11
                            },
                            'artists': [{'name': 'Dua Lipa', 'id': '6M2wZ9GZgrQXHCFfjv46we'}],
                            'duration_ms': 183274,
                            'explicit': False,
                            'id': '5nujrmhLynf4yMoMtj8AQF',
                            'name': 'Levitating',
                            'popularity': 87,
                            'track_number': 5,
                            'type': 'track'
                        }
                    ],
                    'limit': 50,
                    'next': None,
                    'offset': 150,
                    'previous': 'https://api.spotify.com/v1/search?q=pop&type=track&limit=50&offset=100',
                    'total': 200
                }
            },
            status=200
        )

        resp.add(
            responses.GET,
            'https://api.spotify.com/search?q=nonexistent&type=track&limit=50&offset=0',
            json={'tracks': {'items': [] }},
            status=200
        )

        yield resp


@pytest.fixture
def mock_complete_spotify_pipeline(mock_spotify_token, mock_spotify_track_api, mock_database_connection):
    yield




################################
# LASTFM FIXTURES
################################

@pytest.fixture
def mock_lastfm_api_key(monkeypatch):
    monkeypatch.setenv('LASTFM_API_KEY', 'your_api_key')
    

@pytest.fixture
def mock_complete_lastfm_pipeline(mock_lastfm_api_key, mock_lastfm_api):
    yield





@pytest.fixture
def expected_lastfm_extracted_data():
    return {
        'song_name': 'as it was',
        'artist_name': 'harry styles',
        'listeners': 1250000,
        'original_song_name': 'as it was',
        'original_artist_name': 'harry styles',
        'artist_id': '6KImCVD70vtIoJWnq6nGn3',
        'song_id': '4Dvkj6JhhA12EX05fT7y2e',
        'source': 'Lastfm'
    }


@pytest.fixture
def expected_lastfm_transformed_data():
    return {
        'song_name': 'as it was',
        'artist_name': 'harry styles',
        'artist_id': '6KImCVD70vtIoJWnq6nGn3',
        'num_song_listeners': 1250000,
        'mbid': '12345678-abcd-1234-5678-123456789012',
        'on_tour': False,
        'artist_total_listeners': 8500000,
        'artist_total_playcount': 120000000,
        'song_id': '4Dvkj6JhhA12EX05fT7y2e',
        'source': 'Lastfm',
        'engagement_ratio': 0.14706,
        'plays_per_listener': 14.11765
    }


@pytest.fixture
def expected_lastfm_matched_data(expected_lastfm_extracted_data):
    matched = expected_lastfm_extracted_data.copy()
    matched['mbid'] = '12345678-abcd-1234-5678-123456789012'
    matched['on_tour'] = 0
    matched['artist_listeners'] = 8500000
    matched['artist_playcount'] = 120000000
    matched['source'] = 'Lastfm'
    return matched


@pytest.fixture
def invalid_lastfm_transformed_track(expected_lastfm_transformed_data):
    data = expected_lastfm_transformed_data.copy()
    data.pop('song_id', None)
    return data


@pytest.fixture
def nullified_lastfm_transformed_track(expected_lastfm_transformed_data):
    data = expected_lastfm_transformed_data.copy()
    data['artist_id'] = None
    return data



@pytest.fixture
def mock_lastfm_api():

    responses.start()
    responses.add(
        responses.GET,
        'http://ws.audioscrobbler.com/2.0/?method=track.search&track=as%20it%20was%20harry%20styles&api_key=your_api_key&format=json&limit=5',
        json={
            "results": {
                "trackmatches": {
                    "track": [
                        {
                            "name": "As It Was",
                            "artist": "Harry Styles",
                            "listeners": "1250000"
                        }
                    ]
                }
            }
        },
        status=200
    )
    responses.add(
    responses.GET,
    'http://ws.audioscrobbler.com/2.0/?method=artist.getInfo&api_key=your_api_key&artist=harry+styles&format=json&limit=5',
    json={
        "artist": {
            "name": "Harry Styles",
            "mbid": "12345678-abcd-1234-5678-123456789012",
            "url": "https://www.last.fm/music/Harry+Styles",
            "on_tour": 0,
            "stats": {
                "listeners": 8500000,
                "playcount": 120000000
            }
        }
    },
    status=200
)

    
    responses.add(
        responses.GET,
        'http://ws.audioscrobbler.com/2.0/?method=track.search&track=nonexistent%20song%20unknown%20artist&api_key=your_api_key&format=json&limit=5',
        json={
            "results": {
                "trackmatches": {
                    "track": []  
                }
            }
        },
        status=200
    )


    yield
    responses.stop()
    responses.reset()










################################
# SPOTIFY ARTIST FIXTURES
################################

@pytest.fixture
def mock_spotify_artist_api():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as resp:
        resp.add(
            responses.GET,
            'https://api.spotify.com/v1/artists/4Dvkj6JhhA12EX05fT7y2e',
            json={
                'followers': {'total': 123456},
                'popularity': 85,
                'id': '4Dvkj6JhhA12EX05fT7y2e',
                'name': 'Harry Styles',
                'genres': ['pop', 'rock']
            },
            status=200
        )
        yield resp




@pytest.fixture
def expected_extracted_spotify_artist():
    return {
        'follower_count':  123456,
        'popularity': 85,
        'artist_id': '4Dvkj6JhhA12EX05fT7y2e',
        'artist_name': 'Harry Styles',
        'genres': ['pop', 'rock'],
        'source': 'artist_genre'
    }

@pytest.fixture
def expected_transformed_spotify_artist():
    return {
        'followers':  123456,
        'popularity': 85,
        'artist_id': '4Dvkj6JhhA12EX05fT7y2e',
        'artist_name': 'harry styles',
        'genres': ['pop', 'rock'],
        'source': 'artist_genre',
        'has_genres': True
    }


@pytest.fixture
def invalid_spotify_artist_missing_field(expected_transformed_spotify_artist):
    data = expected_transformed_spotify_artist.copy()
    data.pop('artist_id', None)
    return data


@pytest.fixture
def invalid_spotify_artist_null_field(expected_transformed_spotify_artist):
    data = expected_transformed_spotify_artist.copy()
    data['artist_name'] = None
    return data









################################
# AUDIO FEATURES FIXTURES
################################

@pytest.fixture
def mock_librosa(monkeypatch):
    class DummyBeat:
        @staticmethod
        def beat_track(y, sr):
            return 172.265625, [1]
    class DummyFeature:
        @staticmethod
        def rms(y):
            return [0.306]  # energy mean ~0.153
        @staticmethod
        def spectral_centroid(y, sr):
            return [1895.619]
    class DummyZCR:
        @staticmethod
        def zero_crossing_rate(y):
            return [0.06824898544295478]
    class DummyHPSS:
        @staticmethod
        def hpss(y):
            return np.array([1.0]), np.array([0.4])
    monkeypatch.setattr('src.extract.audio_features_extractor.librosa.beat.beat_track', DummyBeat.beat_track)
    monkeypatch.setattr('src.extract.audio_features_extractor.librosa.feature.rms', DummyFeature.rms)
    monkeypatch.setattr('src.extract.audio_features_extractor.librosa.feature.spectral_centroid', DummyFeature.spectral_centroid)
    monkeypatch.setattr('src.extract.audio_features_extractor.librosa.feature.zero_crossing_rate', DummyZCR.zero_crossing_rate)
    monkeypatch.setattr('src.extract.audio_features_extractor.librosa.effects.hpss', DummyHPSS.hpss)


def generate_sine_wave(duration_seconds=1, rate=22050, freq=440.0):
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        max_amplitude = 32767
        frames = bytearray()
        for i in range(int(rate * duration_seconds)):
            sample = int(max_amplitude * math.sin(2 * math.pi * freq * i / rate))
            frames.extend(struct.pack('<h', sample))
        wf.writeframes(frames)
    return buffer.getvalue()


@pytest.fixture
def valid_audio_features():
    return{
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
def mock_audio_features_api():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as resp:
        resp.add(
            responses.GET,
            'https://audio_features.com/as_it_was',
            body=generate_sine_wave(),
            status=200,
            content_type='audio/mpeg'
        )
        yield resp


@pytest.fixture
def mock_audio_features_finder(monkeypatch):
    preview_payload = {
        'results': [{'previewUrl': 'https://audio_features.com/as_it_was'}],
        'success': True
    }
    class DummyFinder:
        def search_and_get_links(self, *args, **kwargs):
            return preview_payload
    monkeypatch.setattr('src.extract.audio_features_extractor.finder', DummyFinder())
    return preview_payload


@pytest.fixture
def expected_extracted_audio_features_data():
    return {
        'song_id': '4Dvkj6JhhA12EX05fT7y2e',
        'bpm': 172.265625,
        'energy': 0.306,
        'spectral_centroid': 1895.6191806047316,
        'zero_crossing_rate': 0.06824898544295478,
        'preview_url': 'https://audio_features.com/as_it_was',
        'harmonic_ratio': 0.7142857142857143,
        'percussive_ratio': 0.28571428571428575,
        'source': 'preview_url'
    }


@pytest.fixture
def expected_audio_features_transformed_data():
    bpm = 172.265625
    energy = 0.306
    zero_crossing_rate = 0.06824898544295478
    tempo_normalized = min(bpm / 200, 1.0)
    danceability = round((tempo_normalized * 0.3) + (energy * 0.5) + (zero_crossing_rate * 0.2), 5)
    return {
        'song_id': '4Dvkj6JhhA12EX05fT7y2e',
        'bpm': round(bpm, 3),
        'energy': round(energy, 5),
        'spectral_centroid': round(1895.6191806047316, 3),
        'zero_crossing_rate': round(zero_crossing_rate, 5),
        'danceability': danceability,
        'preview_url': 'https://audio_features.com/as_it_was',
        'harmonic_ratio': 0.71429,
        'percussive_ratio': 0.28571,
        'source': 'preview_url'
    }


@pytest.fixture
def invalid_audio_features_missing_field(valid_audio_features):
    data = valid_audio_features.copy()
    data.pop('song_id')
    return data


@pytest.fixture
def invalid_audio_features_null_field(valid_audio_features):
    data = valid_audio_features.copy()
    data['song_id'] = None
    return data




















@pytest.fixture
def valid_spotify_data()-> dict:
    return{
        'album_type': 'single',
        'is_playable': True,
        'album_id': '1234567890abcdefghijk1',
        'song_name': 'Test Song ',
        'artist_name': 'Test Artist',
        'release_date': '2023-02-02',
        'release_date_precision': 'day',
        'album_total_tracks': 99,
        'track_number':3,
        'is_explicit': True,
        'popularity': 70,
        'song_id': '1io456789012aer6789012',
        'duration_ms': 600000,
        'duration_seconds' : 600,
        'duration_minutes' : 10.0,
        'artist_id' : 'wer45poiup1234567nnpp2',
        'album_title': 'Test Album'
        }

@pytest.fixture
def valid_lastfm_data():
    return{
        'song_name': 'Test Song ',
        'artist_name': 'Test Artist',
        'num_song_listeners': 50000,

        'mbid': '12345678-abc3-4d4c-0b90-0987654321ab',
        'on_tour': False,
        'song_id': '21lop6789fyt385Yt890ab',
        'artist_total_playcount': 100000,
        'artist_total_listeners': 200000,
        'plays_per_listener': .5,
        'engagement_ratio':.25,
        'artist_id': '1Er4567890BOutf6789012'
        }




