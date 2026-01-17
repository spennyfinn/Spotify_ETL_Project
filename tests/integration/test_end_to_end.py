

from pydantic import ValidationError
import pytest
from src.extract.spotify_track_extractor import extract_batch_spotify_data
from src.extract.lastfm_extractor import match_artists_from_lastfm, get_track_from_lastfm
from src.extract.audio_features_extractor import get_audio_features
from src.transform.data_transformer import (transform_spotify_artist_data, transform_audio_features_data, transform_lastfm_data,
                                           transform_spotify_data)
from src.utils.spotify_api_utils import (insert_audio_features_query, insert_genres_query, lastfm_artist_query,
                                        lastfm_song_query, spotify_album_query,
                                        spotify_artist_query, spotify_song_query, insert_artist_data_query)
from src.validate.artist_validator import ArtistData
from src.validate.audio_features_validator import AudioFeaturesData
from src.validate.lastfm_validator import LastFmData
from src.validate.spotify_track_validator import SpotifyTrackData
from src.load.data_loader import (load_artist_data_batch, load_audio_features_batch,
                                  load_spotify_data_batch, load_lastfm_data_batch)

from src.extract.spotify_artist_extractor import extract_spotify_artist_metrics



class TestSpotifyPipeline():


    def assert_extracted_track(self, track, expectation):
        for key in track.keys():
            assert track[key]== expectation[key]


    def assert_transformed_track(self, transformed_data, transformed_expected):
        assert type(transformed_data) is dict
        assert len(transformed_data) == 18

        for key in transformed_data.keys():
            assert transformed_data[key]== transformed_expected[key]

    
        
    def assert_load_spotify_batch(self, transformed_tracks, cursor):
        success, error = load_spotify_data_batch(transformed_tracks, cursor)
        assert error == 0
        assert success == len(transformed_tracks) * 3
        assert cursor.executemany.call_count == 3
        calls = cursor.executemany.call_args_list
        assert calls[0][0][0] == spotify_artist_query
        assert calls[1][0][0] == spotify_album_query
        assert calls[2][0][0] == spotify_song_query
        return success, error





    def test_successful_spotify_e2e(self, mock_complete_spotify_pipeline, mock_database_connection, expected_spotify_data_extracted, expected_transformed_spotify_data):
        mock_cur = mock_database_connection
        all_tracks=[]
        tracks = extract_batch_spotify_data(['pop'])

        assert len(tracks) == 4
        assert all(track is not None for track in tracks)
        assert all(type(track) is dict for track in tracks)

        for track in tracks:
            song_name = track.get('name').lower()
            expectation = expected_spotify_data_extracted.get(song_name)
            assert expectation is not None, f'unexpected track: {song_name}'

            try:
                self.assert_extracted_track(track, expectation)
            except Exception as e:
                pytest.fail(f'There was an error in the extraction for track: {song_name}: {e}')

            try:
                transformed_data = transform_spotify_data(track)
                transformed_expected = expected_transformed_spotify_data[song_name]
                self.assert_transformed_track(transformed_data, transformed_expected)

            except Exception as e:
                pytest.fail(f'There was an error in the transform step for {song_name}: {e}')

            try:
                SpotifyTrackData(**transformed_data)
            except Exception as e:
                pytest.fail(f'Validation raised unexpectedly for song: {song_name}: {e}')
            all_tracks.append(transformed_data)
        try:       
            self.assert_load_spotify_batch(all_tracks, mock_cur)
            
        except Exception as e:
            pytest.fail(f'Loading raised an unexpected error: {e}')


    def test_missing_req_fields_transformed_spotify_data(self, invalid_spotify_transformed_track, nullified_spotify_transformed_track):
        for test_data in [invalid_spotify_transformed_track,nullified_spotify_transformed_track]:
            none_data = transform_spotify_data(test_data)
            assert none_data == None

    def test_missing_req_fields_validation_spotify_data(self, invalid_spotify_transformed_track, nullified_spotify_transformed_track):
        for test_data in [invalid_spotify_transformed_track,nullified_spotify_transformed_track]:
            with pytest.raises((ValidationError, TypeError)):
                SpotifyTrackData(**test_data)

    def test_missing_req_fields_load_spotify_data(self, invalid_spotify_transformed_track, nullified_spotify_transformed_track, mock_database_connection):
        mock_cur = mock_database_connection
        with pytest.raises(ValueError):
            success, error = load_spotify_data_batch([invalid_spotify_transformed_track, nullified_spotify_transformed_track], mock_cur)






class TestLastFmPipeline():

    def assert_extracted_track_lastfm(self, lastfm_data, expected):
        assert lastfm_data
        assert type(lastfm_data) is dict
        assert len(lastfm_data)==7
        for key in lastfm_data.keys():
            assert lastfm_data[key] == expected[key]

    def assert_matched_artist_lastfm(self, data, expected_data):
        assert data
        assert type(data) is dict
        print(data)
        assert len(data) ==  12
        for key in data.keys():
            assert data[key] == expected_data[key]
        
 
    def assert_transformed_track_lastfm(self, transformed_data, expected):
        assert type(transformed_data) is dict
        assert transformed_data
        assert len(transformed_data)==12
        for key in transformed_data.keys():
            assert transformed_data[key] == expected[key]

    def assert_load_lastfm_batch(self, success, error, mock_cur):
        assert success==2
        assert error ==0
        assert mock_cur.executemany.call_count==2
        calls = mock_cur.executemany.call_args_list
        assert calls[0][0][0] == lastfm_artist_query
        assert calls[1][0][0] == lastfm_song_query





    def test_complete_lastfm_pipeline(self, mock_complete_lastfm_pipeline, mock_database_connection, expected_lastfm_extracted_data, expected_lastfm_transformed_data, expected_lastfm_matched_data):
        mock_cur = mock_database_connection
        try:
            lastfm_data = get_track_from_lastfm('as it was', 'harry styles', '4Dvkj6JhhA12EX05fT7y2e', '6KImCVD70vtIoJWnq6nGn3', 'your_api_key')
            self.assert_extracted_track_lastfm(lastfm_data, expected_lastfm_extracted_data)
        except Exception as e:
            pytest.fail(f"There was an unexpected error during extraction: {e}")
        
        artist_data = match_artists_from_lastfm(lastfm_data, 'your_api_key')
        self.assert_matched_artist_lastfm(artist_data, expected_lastfm_matched_data)
        
        try:
            transformed_data=transform_lastfm_data(artist_data)
            self.assert_transformed_track_lastfm(transformed_data, expected_lastfm_transformed_data)
        except Exception as e:
            pytest.fail(f"There was an unexpected error during transformations: {e}")

        try:
            LastFmData(**transformed_data)
        except Exception as e:
            pytest.fail(f"There was an unexpected error during extraction: {e}")

        success, error=load_lastfm_data_batch([transformed_data], mock_cur)
        self.assert_load_lastfm_batch(success, error, mock_cur)
        

  
    def test_missing_req_fields_transformed_lastfm_data(self, invalid_lastfm_transformed_track, nullified_lastfm_transformed_track):
        for test_data in [invalid_lastfm_transformed_track,nullified_lastfm_transformed_track]:
            none_data = transform_lastfm_data(test_data)
            assert none_data == None

    def test_missing_req_fields_validation_lastfm_data(self, invalid_lastfm_transformed_track, nullified_lastfm_transformed_track):
        for test_data in [invalid_lastfm_transformed_track,nullified_lastfm_transformed_track]:
            with pytest.raises((ValidationError, TypeError)):
                LastFmData(**test_data)

    def test_missing_req_fields_load_lastfm_data(self, invalid_lastfm_transformed_track, nullified_lastfm_transformed_track, mock_database_connection):
        mock_cur = mock_database_connection
        success, error = load_lastfm_data_batch([invalid_lastfm_transformed_track, nullified_lastfm_transformed_track], mock_cur)
        assert error ==2
        assert success ==0

    

class TestAudioFeaturesPipeline():

    def assert_audio_features_fixtures(self, data, expected):
        assert data
        assert isinstance(data, dict)
        assert len(data) == len(expected)
        for key, value in expected.items():
            if isinstance(value, float):
                assert data[key] == pytest.approx(value, rel=1e-6)
            else:
                assert data[key] == value

    def assert_load_audio_features(self, success, error,  mock_cur):
        assert success==9
        assert error==0
        assert mock_cur.executemany.call_count==1
        calls = mock_cur.executemany.call_args_list
        assert calls[0][0][0] == insert_audio_features_query
        


    def test_complete_audio_features_pipeline(
        self,
        mock_database_connection,
        mock_audio_features_api,
        mock_audio_features_finder,
        mock_librosa,
        expected_extracted_audio_features_data,
        expected_audio_features_transformed_data
    ):
        mock_cur = mock_database_connection
        try:
            data = get_audio_features('as it was', 'harry styles', '4Dvkj6JhhA12EX05fT7y2e')
            self.assert_audio_features_fixtures(data, expected_extracted_audio_features_data)
        except Exception as e:
            pytest.fail(f'There was an error in audio feature extraction: {e}')

        try:
            transformed_data = transform_audio_features_data(data)
            self.assert_audio_features_fixtures(transformed_data, expected_audio_features_transformed_data)
        except Exception as e:
            pytest.fail(f'There was an error in audio feature transformation: {e}')

        try:
            AudioFeaturesData(**transformed_data)
        except Exception as e:
            pytest.fail(f'There was an unexpected error while validating audio features data: {e}')

        try:
            success, error = load_audio_features_batch([transformed_data], mock_cur)
            self.assert_load_audio_features(success, error, mock_cur)
        except Exception as e:
            pytest.fail(f'Audio feature loading raised unexpectedly: {e}')

    def test_missing_req_fields_transformed_audio_features_data(self, invalid_audio_features_missing_field, invalid_audio_features_null_field):
        for test_data in [invalid_audio_features_missing_field,invalid_audio_features_null_field]:
            none_data = transform_audio_features_data(test_data)
            assert none_data == None

    def test_missing_req_fields_validation_audio_features_data(self, invalid_audio_features_missing_field, invalid_audio_features_null_field):
        for test_data in [invalid_audio_features_missing_field,invalid_audio_features_null_field]:
            with pytest.raises((ValidationError, TypeError)):
                AudioFeaturesData(**test_data)

    def test_missing_req_fields_load_audio_features_data(self, invalid_audio_features_missing_field, invalid_audio_features_null_field, mock_database_connection):
        mock_cur = mock_database_connection
        success, error = load_audio_features_batch([invalid_audio_features_missing_field, invalid_audio_features_null_field], mock_cur)
        assert error ==2
        assert success ==0


    
        
class TestSpotifyArtistPipeline():
    
    

    def assert_spotify_artist_fixtures(self, data, expected):
        assert data
        assert isinstance(data, dict)
        assert len(data) == len(expected)
        for key in expected.keys():

            assert data[key] == expected[key]

    def assert_load_spotify_artist(self, load_result, mock_cur):
        a_success, a_error, g_success, g_error, ag_success, ag_error = load_result
        assert a_success == 1
        assert a_error == 0
        assert g_success == 2
        assert g_error == 0
        assert ag_success == 2
        assert ag_error == 0
        assert mock_cur.executemany.call_count == 2
        calls = mock_cur.executemany.call_args_list
        assert calls[0][0][0] == insert_artist_data_query
        assert calls[1][0][0] == insert_genres_query



    def test_complete_spotify_artist_pipeline(self, mock_database_connection, mock_spotify_artist_api, mock_spotify_token,expected_extracted_spotify_artist, expected_transformed_spotify_artist ):
        mock_cur = mock_database_connection

        try:
            data = extract_spotify_artist_metrics('4Dvkj6JhhA12EX05fT7y2e','harry styles')
            self.assert_spotify_artist_fixtures(data, expected_extracted_spotify_artist)
        except Exception as e:
            pytest.fail(f'There was an unexpected error while validating Spotify Artist data : {e}')
        
        
        try:
            transformed_data = transform_spotify_artist_data(data)
            self.assert_spotify_artist_fixtures(transformed_data, expected_transformed_spotify_artist)
        except Exception as e:
            pytest.fail(f'There was an unexpected error while validating Spotify Artist data : {e}')
        
        
        try:
            ArtistData(**transformed_data)
        except Exception as e:
            pytest.fail(f'There was an unexpected error while validating Spotify Artist data : {e}')

        try:
            mock_cur.fetchall.return_value = [('pop', 1), ('rock', 2)]
            load_result = load_artist_data_batch([transformed_data], mock_cur)
            self.assert_load_spotify_artist(load_result, mock_cur)
        except Exception as e:
            pytest.fail(f'Spotify Artist data loading raised unexpectedly: {e}')

    def test_missing_req_fields_transformed_lastfm_data(self, invalid_spotify_artist_missing_field, invalid_spotify_artist_null_field):
        for test_data in [invalid_spotify_artist_missing_field,invalid_spotify_artist_null_field]:
            none_data = transform_spotify_artist_data(test_data)
            assert none_data == None

    def test_missing_req_fields_validation_lastfm_data(self, invalid_spotify_artist_missing_field, invalid_spotify_artist_null_field):
        for test_data in [invalid_spotify_artist_missing_field,invalid_spotify_artist_null_field]:
            with pytest.raises((ValidationError, TypeError)):
                ArtistData(**test_data)

    def test_missing_req_fields_load_spotify_artist_data(self, invalid_spotify_artist_missing_field, invalid_spotify_artist_null_field, mock_database_connection):
        mock_cur = mock_database_connection
        artist_success_count, artist_error_count,genre_success_count,genre_error_count,artist_genre_success_count,artist_genre_error_count = load_artist_data_batch([invalid_spotify_artist_missing_field, invalid_spotify_artist_null_field], mock_cur)
        assert artist_success_count==0
        assert artist_error_count==0
        assert genre_success_count ==0
        assert genre_error_count==0
        assert artist_genre_success_count ==0
        assert artist_genre_error_count ==0


