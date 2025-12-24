from typing import Any
import pytest
import responses
import json
from src.transform.data_transformer import transform_spotify_data
from src.extract.spotify_extractor import extract_main_spotify_data
from src.validation.spotify import Spotify_Data
from src.load.data_loader import load_spotify_data, load_audio_features, load_last_fm 
from src.utils.database import get_db, get_result_from_db_spotify
from unittest.mock import patch




def test_spotify_pipeline_end_to_end(mock_spotify_api):
    with patch('src.utils.spotify_utils.get_spotify_token', return_value='fake_token_12345'):
        track_data = extract_main_spotify_data(['pop'])
        assert type(track_data) is list
        assert len(track_data)==3
        conn,cur=get_db()
        cur.execute("SELECT COUNT(*) FROM songs")
        initial_song_count = cur.fetchone()[0]
    
        try:
            for track in track_data:
                    assert type(track) is dict
                    assert track['source']== 'Spotify'
                    transformed_data = transform_spotify_data(track)
                    assert type(transformed_data) is dict
                    for field in ['song_name', 'artist_name', 'artist_id', 'album_id', 'album_title', 'duration_ms', 'popularity']:
                        assert field in transformed_data
                
                    validated_data=Spotify_Data(**transformed_data)
                    assert validated_data is not None
                    
                    load_spotify_data(transformed_data, cur)
        
                    results = get_result_from_db_spotify(transformed_data['song_name'],transformed_data['artist_name'])
                    assert results['song_name']== transformed_data['song_name']
                    assert results['album_artist_name'] == transformed_data['artist_name'] == results['artist_artist_name']
                    assert results['song_artist_id']== results['artist_artist_id'] ==transformed_data['artist_id']
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


            cur.execute("SELECT COUNT(*) FROM songs")
            final_song_count = cur.fetchone()[0]
    
            assert final_song_count>=initial_song_count+3
        finally:
            cur.execute("DELETE FROM songs WHERE song_name IN ('as it was', 'heat waves', 'stay')")
            cur.execute("DELETE FROM albums WHERE album_title IN ('harrys house', 'dreamland', 'stay')")
            cur.execute("DELETE FROM artists WHERE artist_name IN ('harry styles', 'glass animals', 'the kid laroi')")
                
            conn.close()
            cur.close()

            

        

        

