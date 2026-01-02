from typing import Any
from numba import none
import psycopg2
from psycopg2.extensions import NoneAdapter
import pytest
import responses
import json
from src.extract.lastfm_extractor import get_track_from_lastfm, match_artists_from_lastfm
from src.transform.data_transformer import transform_lastfm_data, transform_spotify_data
from src.extract.spotify_extractor import extract_main_spotify_data
from src.utils.spotify_utils import extract_spotify_data, get_spotify_token, save_token, load_token
from src.validation.lastfm import LastFm
from src.validation.spotify import Spotify_Data
from src.load.data_loader import load_spotify_data, load_audio_features, load_last_fm 
from src.utils.database import get_db, get_result_from_db_lastfm, get_result_from_db_spotify
from unittest.mock import patch, MagicMock




def test_spotify_pipeline_end_to_end(mock_spotify_api):
    with patch('src.utils.spotify_utils.get_spotify_token', return_value='fake_token_12345'):
        track_data = extract_main_spotify_data(['pop'])
        assert type(track_data) is list
        assert len(track_data)==3
        print(track_data)
        conn,cur=get_db()
       
    
        try:
            for track in track_data:
                    assert type(track) is dict
                    assert track['artist_name'] in ['Harry Styles', 'The Kid Laroi', 'Glass Animals']
                    assert track['album_name'] in ['Harrys House', 'Dreamland', 'Stay']
                    assert track['name'] in ['As It Was', 'Heat Waves', 'Stay']
                    assert track['song_id'] in ['4Dvkj6JhhA12EX05fT7y2e', '0VjIjW4GlUZAMYd2vXMi3b', '5PjdY0CKGZdEuoNab3yDmX']
                    assert track['popularity'] in [92, 88, 85]
                    assert track['duration_ms'] in [167303, 238805, 141805]
                    assert track['explicit'] in [False, True]
                    assert track['track_number'] in [1, 4]
                    assert track['artist_id'] in ['6KImCVD70vtIoJWnq6nGn3', '4yvcSjfu4PC0CYQyLy4wSq', '2tIP7SsRs7vjIcLrU85W8J']
                    assert track['album_id'] in ['5r36AJ6VOJot3ika5YF74k', '4yRXW9BV5RW5R7nKP9fXAW', '4yRXW9BV5RW5R7nKP9fXBW']
                    assert track['album_type'] in ['album', 'single']
                    assert track['release_date'] in ['2022-05-20', '2020-08-07', '2021-07-09']
                    assert track['release_date_precision']=='day'
                    assert track['album_total_tracks'] in [1, 13, 16]
                    assert track['source']== 'Spotify'
                    transformed_data = transform_spotify_data(track)
                    assert type(transformed_data) is dict
                    for field in ['song_name', 'artist_name', 'artist_id', 'album_id', 'album_title', 'duration_ms', 'popularity']:
                        assert field in transformed_data
                        assert transformed_data[field] is not None

                    validated_data=Spotify_Data(**transformed_data)
                    assert validated_data is not None
                    
                    load_spotify_data(transformed_data, cur)
                    
                    
                    results = get_result_from_db_spotify(transformed_data['song_id'],transformed_data['song_name'],transformed_data['artist_name'])
                    
                    assert results['song_name']== transformed_data['song_name']
                    assert transformed_data['artist_name'] == results['artist_artist_name']
                    assert results['song_artist_id']== results['artist_artist_id'] ==transformed_data['artist_id'] == results['album_artist_id'] 
                    assert results['popularity'] == transformed_data['popularity']
                    assert results['is_explicit'] == transformed_data['is_explicit']
                    assert results['is_playable']==transformed_data['is_playable']
                    assert results['song_id'] == transformed_data['song_id']
                    assert results['duration_ms'] == transformed_data['duration_ms']
                    assert results['duration_seconds'] == transformed_data['duration_seconds']
                    assert results['duration_minutes'] == transformed_data['duration_minutes']
                    assert results['release_date']== transformed_data['release_date']
                    assert results['release_date_precision']== transformed_data['release_date_precision']
                    assert results['track_number'] == transformed_data['track_number']
                    assert results['song_album_id'] == transformed_data['album_id']== results['album_album_id']
                    assert results['album_total_tracks'] == transformed_data['album_total_tracks']
                    assert results['album_title'] == transformed_data['album_title']
                    assert results['album_type'] == transformed_data['album_type']


        finally:
            #cur.execute("DELETE FROM songs WHERE song_name IN ('as it was', 'heat waves', 'stay')")
            #cur.execute("DELETE FROM albums WHERE album_title IN ('harrys house', 'dreamland', 'stay')")
            #cur.execute("DELETE FROM artists WHERE artist_name IN ('harry styles', 'glass animals', 'the kid laroi')")
                
            conn.close()
            cur.close()

            
def test_empty_spotify_api_response(mock_spotify_api):
    with patch('src.utils.spotify_utils.get_spotify_token', return_value='fake_token_12345'):
        track_data=extract_main_spotify_data(['nonexistent'])
        assert track_data==[]


def test_spotify_database_connection_failure(mock_spotify_api):
    """Test Spotify database connection failure"""
    from unittest.mock import MagicMock

    with patch('src.utils.spotify_utils.get_spotify_token', return_value='fake_token_12345'):
        track_data = extract_main_spotify_data(['pop'])
        transformed_data = transform_spotify_data(track_data[0])

        # Create mock cursor that raises database error
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.OperationalError('Database connection lost')

        # Test that load_spotify_data handles database errors gracefully
        result = load_spotify_data(transformed_data, mock_cursor)
        assert result is False


def test_last_fm_pipeline_end_to_end(mock_lastfm_api):
    conn, cur = get_db()
    try:
        data = get_track_from_lastfm('As It Was', 'Harry Styles','4Dvkj6JhhA12EX05fT7y2e' , '6KImCVD70vtIoJWnq6nGn3', "your_api_key")

        assert type(data) is dict
        assert len(data)==7
        assert data['song_name']=='as it was'
        assert data['artist_name']=='harry styles'
        assert data['song_id']== '4Dvkj6JhhA12EX05fT7y2e' 
        assert data['artist_id']=='6KImCVD70vtIoJWnq6nGn3'
        assert data['original_artist_name']== 'Harry Styles'
        assert data['original_song_name']=='As It Was'
        assert data['listeners']==1250000

        artist_data = match_artists_from_lastfm(data, 'your_api_key')
        assert type(artist_data) is dict
        assert len(artist_data)==12
        assert artist_data['mbid']== '12345678-abcd-1234-5678-123456789012'
        assert artist_data['on_tour'] == 0
        assert artist_data['artist_listeners']== 8500000
        assert artist_data['artist_playcount'] == 120000000
        assert artist_data['source']=='Lastfm'


        transformed_data= transform_lastfm_data(artist_data)
        assert transformed_data['song_name']=='as it was'
        assert transformed_data['artist_name']=='harry styles'
        assert transformed_data['song_id']== '4Dvkj6JhhA12EX05fT7y2e'
        assert transformed_data['artist_id']=='6KImCVD70vtIoJWnq6nGn3'
        assert transformed_data['num_song_listeners']==1250000
        assert transformed_data['mbid']== "12345678-abcd-1234-5678-123456789012"
        assert transformed_data['on_tour'] == False
        assert transformed_data['artist_total_listeners']== 8500000
        assert transformed_data['artist_total_playcount'] == 120000000
        assert transformed_data['source']=='Lastfm'
        assert transformed_data['engagement_ratio']== round(float(transformed_data['num_song_listeners']/transformed_data['artist_total_listeners']),5)
        assert transformed_data['plays_per_listener']== round(float(transformed_data['artist_total_playcount']/transformed_data['artist_total_listeners']),5)

        validated_data=LastFm(**transformed_data)
        assert validated_data is not None
        assert validated_data.song_name=='as it was'
        assert validated_data.artist_name=='harry styles'
        assert validated_data.song_id== '4Dvkj6JhhA12EX05fT7y2e'
        assert validated_data.artist_id=='6KImCVD70vtIoJWnq6nGn3'
        assert validated_data.num_song_listeners==1250000
        assert validated_data.mbid== "12345678-abcd-1234-5678-123456789012"
        assert validated_data.on_tour == False
        assert validated_data.artist_total_listeners== 8500000
        assert validated_data.artist_total_playcount == 120000000
        assert validated_data.engagement_ratio== round(float(validated_data.num_song_listeners/validated_data.artist_total_listeners),5)
        assert validated_data.plays_per_listener== round(float(validated_data.artist_total_playcount/validated_data.artist_total_listeners),5)

        success=load_last_fm(transformed_data, cur)
        assert success

        res= get_result_from_db_lastfm('as it was', 'harry styles')
        assert res['song_name']== transformed_data['song_name']
        assert res['song_id'] == transformed_data['song_id']
        assert res['song_listeners']== transformed_data['num_song_listeners']
        assert res['song_artist_id'] == transformed_data['artist_id'] == res['artist_artist_id']
        assert res['mbid']== transformed_data['mbid']
        assert res['engagement_ratio'] == transformed_data['engagement_ratio']
        assert res['artist_name']== transformed_data['artist_name']
        assert res['total_listeners'] == transformed_data['artist_total_listeners']
        assert res['total_playcount']== transformed_data['artist_total_playcount']
        assert res['plays_per_listener'] == transformed_data['plays_per_listener']
        assert res['on_tour']==transformed_data['on_tour']
    finally:
        conn.close()
        cur.close()
    

def test_empty_lastfm_api_response(mock_lastfm_api):
        track_data=get_track_from_lastfm('nonexistent song', 'unknown artist', '1234567890123456789012', '1234567890123456789012', 'your_api_key')
        print(f'PRINT: {track_data}')
        assert track_data == None


def test_lastfm_database_connection_failure(mock_lastfm_api):
    from unittest.mock import MagicMock

    track_data = get_track_from_lastfm('As It Was', 'Harry Styles','4Dvkj6JhhA12EX05fT7y2e' , '6KImCVD70vtIoJWnq6nGn3', "your_api_key")
    assert track_data is not None
    track_data = match_artists_from_lastfm(track_data, 'your_api_key')
    transformed_data = transform_lastfm_data(track_data)

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = psycopg2.OperationalError('Database connection lost')
    
    with pytest.raises(psycopg2.OperationalError):
        load_last_fm(transformed_data, mock_cursor)