import pytest
import responses
import json




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

@pytest.fixture
def mock_spotify_api():
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
                    'next': None,
                    'offset': 100,
                    'previous': 'https://api.spotify.com/v1/search?q=pop&type=track&limit=50&offset=50',
                    'total': 150
                }
            },
            status=200
        )


        resp.add(
            responses.GET,
            'https://accounts.spotify.com/api/token',
            json={'error': 'invalid_client'},
            status=400
        )
        

        resp.add(
            responses.POST,
            'https://accounts.spotify.com/api/token',
            json={'access_token': 'fake_token_12345', 'token_type': 'Bearer', 'expires_in': 3600},
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


import pytest


@pytest.fixture
def data():
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

