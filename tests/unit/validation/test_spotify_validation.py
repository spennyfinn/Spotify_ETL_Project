
import pytest
from src.validation.spotify import Spotify_Data
from tests.unit.constants import (
    VALID_BOOLEAN_VALUES, VALID_DURATION_VALUES, VALID_DURATION_VALUES_IDS, VALID_TRACK_NUMBER_VALUES,
    WRONG_FLOAT_TYPE, WRONG_FLOAT_TYPE_IDS, INVALID_ID_IDS, INVALID_IDS,
    WRONG_BOOLEAN_TYPES, WRONG_BOOLEAN_TYPES_IDS, WRONG_INT_TYPE, WRONG_INT_TYPE_IDS,
    WRONG_STRING_TYPE, WRONG_STRING_TYPE_IDS, EMPTY_STRINGS, EMPTY_STRINGS_IDS
)


class TestSpotifyValidation:

    

    #POPULARITY
    @pytest.mark.parametrize('value', VALID_TRACK_NUMBER_VALUES.copy()+[0], ids=VALID_TRACK_NUMBER_VALUES.copy()+[0])
    def test_popularity_boundaries(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['popularity'] = value
        data = Spotify_Data(**test_data)
        assert data.popularity == value

    @pytest.mark.parametrize('value', [-1, -100, 101, 150])
    def test_popularity_out_of_range(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['popularity'] = value
        with pytest.raises(ValueError, match='popularity'):
            Spotify_Data(**test_data)
    
    @pytest.mark.parametrize('value', WRONG_INT_TYPE, ids=WRONG_INT_TYPE_IDS)
    def test_popularity_wrong_types(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['popularity'] = value
        with pytest.raises(TypeError, match='popularity'):
            Spotify_Data(**test_data)

    #SONG NAME
    def test_valid_song_names(self, valid_spotify_data):
        data=Spotify_Data(**valid_spotify_data)
        assert data.song_name.lower().strip()== 'test song'

    @pytest.mark.parametrize('value', EMPTY_STRINGS, ids=EMPTY_STRINGS_IDS)
    def test_invalid_strings_song_names(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['song_name'] = value
        with pytest.raises(ValueError, match='song_name'):
            Spotify_Data(**test_data)

    @pytest.mark.parametrize('value', WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_invalid_types_song_names(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['album_title'] = value
        with pytest.raises(TypeError, match='album_title'):
            Spotify_Data(**test_data)

    #ARTIST NAMES:
    def test_valid_artist_names(self, valid_spotify_data):
        data=Spotify_Data(**valid_spotify_data)
        assert data.artist_name.lower().strip()== 'test artist'

    @pytest.mark.parametrize('value', EMPTY_STRINGS, ids=EMPTY_STRINGS_IDS)
    def test_invalid_strings_artist_names(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['artist_name'] = value
        with pytest.raises(ValueError, match='artist_name'):
            Spotify_Data(**test_data)

    @pytest.mark.parametrize('value', WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_invalid_types_artist_names(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['artist_name'] = value
        with pytest.raises(TypeError, match='artist_name'):
            Spotify_Data(**test_data)


    #ALBUM TITLE
    def test_valid_album_titles(self, valid_spotify_data):
        data=Spotify_Data(**valid_spotify_data)
        assert data.album_title.lower().strip()=='test album'

    @pytest.mark.parametrize('value', EMPTY_STRINGS, ids=EMPTY_STRINGS_IDS)
    def test_invalid_strings_album_title(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['album_title'] = value
        with pytest.raises(ValueError, match='album_title'):
            Spotify_Data(**test_data)

    @pytest.mark.parametrize('value', WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_invalid_types_album_title(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['album_title'] = value
        with pytest.raises(TypeError, match='album_title'):
            Spotify_Data(**test_data)



    #IDS
    def test_valid_ids(self, valid_spotify_data):
        data = Spotify_Data(**valid_spotify_data)

        assert data.album_id == valid_spotify_data['album_id']
        assert data.song_id == valid_spotify_data['song_id'] 
        assert data.artist_id == valid_spotify_data['artist_id']

    #ARTIST IDS
    @pytest.mark.parametrize('value', INVALID_IDS, ids=INVALID_ID_IDS )
    def test_invalid_inputs_artist_ids(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['artist_id'] = value
        with pytest.raises(ValueError, match='artist_id'):
            Spotify_Data(**test_data)

    @pytest.mark.parametrize('value', WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_invalid_types_artist_ids(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['album_id'] = value
        with pytest.raises(TypeError, match='album_id'):
            Spotify_Data(**test_data)
    
    
    #SONG IDS
    @pytest.mark.parametrize('value', INVALID_IDS, ids=INVALID_ID_IDS)
    def test_invalid_inputs_song_ids(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['song_id'] = value
        with pytest.raises(ValueError, match='song_id'):
            Spotify_Data(**test_data)
                
    @pytest.mark.parametrize('value', WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_invalid_types_song_ids(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['song_id'] = value
        with pytest.raises(TypeError, match='song_id'):
            Spotify_Data(**test_data)


    #ALBUM IDS
    @pytest.mark.parametrize('value',INVALID_IDS, ids=INVALID_ID_IDS)
    def test_invalid_inputs_album_ids(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['album_id'] = value
        with pytest.raises(ValueError, match='album_id'):
            Spotify_Data(**test_data)
                
    @pytest.mark.parametrize('value', WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_invalid_types_album_ids(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['album_id'] = value
        with pytest.raises(TypeError, match='album_id'):
            Spotify_Data(**test_data)

    #DURATION MS
    @pytest.mark.parametrize('value_sec,value_ms,value_min',  VALID_DURATION_VALUES, ids=VALID_DURATION_VALUES_IDS)
    def test_valid_duration_ms(self, valid_spotify_data, value_sec, value_ms, value_min):
        test_data = valid_spotify_data.copy()
        test_data['duration_minutes'] = value_min
        test_data['duration_ms'] = value_ms
        test_data['duration_seconds'] = value_sec
        data = Spotify_Data(**test_data)
        assert data.duration_ms == value_ms
        

    @pytest.mark.parametrize('value', [999, 7200001, 10000000, -100, 0])
    def test_invalid_inputs_duration_ms(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['duration_ms'] = value
        with pytest.raises(ValueError, match='duration_ms'):
            Spotify_Data(**test_data)
                
    @pytest.mark.parametrize('value', WRONG_INT_TYPE, ids=WRONG_INT_TYPE_IDS)
    def test_invalid_types_duration_ms(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['duration_ms'] = value
        with pytest.raises(TypeError, match='duration_ms'):
            Spotify_Data(**test_data)


    #DURATION SECONDS
    @pytest.mark.parametrize('value_sec,value_ms,value_min',  VALID_DURATION_VALUES, ids=VALID_DURATION_VALUES_IDS)
    def test_valid_duration_seconds(self, valid_spotify_data, value_sec, value_ms, value_min):
        test_data = valid_spotify_data.copy()
        test_data['duration_minutes'] = value_min
        test_data['duration_ms'] = value_ms
        test_data['duration_seconds'] = value_sec
        data = Spotify_Data(**test_data)
        assert data.duration_seconds == value_sec
        

    @pytest.mark.parametrize('value', [7201, 10000, -100, 0])
    def test_invalid_inputs_duration_seconds(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['duration_seconds'] = value
        with pytest.raises(ValueError, match='duration_seconds'):
            Spotify_Data(**test_data)
                
    @pytest.mark.parametrize('value',  WRONG_INT_TYPE, ids=WRONG_INT_TYPE_IDS)
    def test_invalid_types_duration_seconds(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['duration_seconds'] = value
        with pytest.raises(TypeError, match='duration_seconds'):
            Spotify_Data(**test_data)

    #DURATION MINUTES
    @pytest.mark.parametrize('value_sec,value_ms,value_min', VALID_DURATION_VALUES, ids=VALID_DURATION_VALUES_IDS )
    def test_valid_duration_minutes(self, valid_spotify_data, value_sec, value_ms, value_min):
        test_data = valid_spotify_data.copy()
        test_data['duration_minutes'] = value_min
        test_data['duration_ms'] = value_ms
        test_data['duration_seconds'] = value_sec
        data = Spotify_Data(**test_data)
        assert data.duration_minutes == value_min
        

    @pytest.mark.parametrize('value', [.016, 120.0, -100.0, 0.0, 200.0])
    def test_invalid_inputs_duration_minutes(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['duration_minutes'] = value
        with pytest.raises(ValueError, match='duration_minutes'):
            Spotify_Data(**test_data)
                
    @pytest.mark.parametrize('value',  WRONG_FLOAT_TYPE, ids=WRONG_FLOAT_TYPE_IDS)
    def test_invalid_types_duration_minutes(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['duration_minutes'] = value
        with pytest.raises(TypeError, match='duration_minutes'):
            Spotify_Data(**test_data)

    #MODEL CALCULATIONS:
    def test_duration_inconsistency_validation(self, valid_spotify_data):
        test_data = valid_spotify_data.copy()
        test_data['duration_seconds'] = 100
        with pytest.raises(ValueError, match='duration'):
            Spotify_Data(**test_data)

     #ALBUM TYPE
    @pytest.mark.parametrize('value', ['album', 'single', 'compilation'])
    def test_valid_album_type(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['album_type'] = value
        data = Spotify_Data(**test_data)
        assert data.album_type == value
        

    @pytest.mark.parametrize('value', EMPTY_STRINGS.copy()+['albu', 'singler', 'compilation@', '12345'])
    def test_invalid_inputs_album_type(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['album_type'] = value
        with pytest.raises(ValueError, match='album_type'):
            Spotify_Data(**test_data)
                
    @pytest.mark.parametrize('value', WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_invalid_types_album_type(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['album_type'] = value
        with pytest.raises(TypeError, match='album_type'):
            Spotify_Data(**test_data)

    #RELEASE_DATE_PRECISION
    @pytest.mark.parametrize('value', ['day', 'month', 'year'])
    def test_valid_date_precision(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['release_date_precision'] = value
        data = Spotify_Data(**test_data)
        assert data.release_date_precision == value
        

    @pytest.mark.parametrize('value', EMPTY_STRINGS.copy()+['da', 'days', 'mont', 'month@', '12345', 'Years', "YER"], ids=EMPTY_STRINGS_IDS.copy()+['da', 'days', 'mont', 'month@', '12345', 'Years', "YER"])
    def test_invalid_inputs_date_precision(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['release_date_precision'] = value
        with pytest.raises(ValueError, match='release_date_precision'):
            Spotify_Data(**test_data)
                
    @pytest.mark.parametrize('value', WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_invalid_types_date_precision(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['release_date_precision'] = value
        with pytest.raises(TypeError, match='release_date_precision'):
            Spotify_Data(**test_data)

    #ALBUM TOTAL TRACKS
    @pytest.mark.parametrize('value', VALID_TRACK_NUMBER_VALUES)
    def test_valid_album_total_tracks(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['album_total_tracks'] = value
        data = Spotify_Data(**test_data)
        assert data.album_total_tracks == value

    def test_validate_return_zero_album_total_tracks(self, valid_spotify_data):
        test_data = valid_spotify_data.copy()
        test_data['album_total_tracks'] = None
        data = Spotify_Data(**test_data)
        assert data.album_total_tracks == 0
    

    @pytest.mark.parametrize('value', [-1, -50, 101, 200])
    def test_invalid_inputs_album_total_tracks(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['album_total_tracks'] = value
        with pytest.raises(ValueError, match='album_total_tracks'):
            Spotify_Data(**test_data)
    
    @pytest.mark.parametrize('value',  WRONG_INT_TYPE[:-1], ids=WRONG_INT_TYPE_IDS[:-1])
    def test_invalid_types_album_total_tracks(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['album_total_tracks'] = value
        with pytest.raises(TypeError, match='album_total_tracks'):
            Spotify_Data(**test_data)

    #IS PLAYABLE
    @pytest.mark.parametrize('value', VALID_BOOLEAN_VALUES)
    def test_valid_is_playable(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['is_playable'] = value
        data = Spotify_Data(**test_data)
        assert data.is_playable == value
    
    @pytest.mark.parametrize('value', WRONG_BOOLEAN_TYPES, ids=WRONG_BOOLEAN_TYPES_IDS)
    def test_invalid_types_is_playable(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['is_playable'] = value
        with pytest.raises(TypeError, match='is_playable'):
            Spotify_Data(**test_data)

    #IS EXPLICIT
    @pytest.mark.parametrize('value', VALID_BOOLEAN_VALUES)
    def test_valid_is_explicit(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['is_explicit'] = value
        data = Spotify_Data(**test_data)
        assert data.is_explicit == value
    
    @pytest.mark.parametrize('value', WRONG_BOOLEAN_TYPES, ids=WRONG_BOOLEAN_TYPES_IDS)
    def test_invalid_types_is_explicit(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['is_explicit'] = value
        with pytest.raises(TypeError, match='is_explicit'):
            Spotify_Data(**test_data)

    #TRACK NUMBER
    @pytest.mark.parametrize('value', VALID_TRACK_NUMBER_VALUES)
    def test_valid_track_number(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['track_number'] = value
        data = Spotify_Data(**test_data)
        assert data.track_number == value
    

    @pytest.mark.parametrize('value', [-1, -50, 101, 200])
    def test_invalid_inputs_track_number(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['track_number'] = value
        with pytest.raises(ValueError, match='track_number'):
            Spotify_Data(**test_data)
    
    @pytest.mark.parametrize('value',  WRONG_INT_TYPE, ids=WRONG_INT_TYPE_IDS)
    def test_invalid_types_track_number(self, valid_spotify_data, value):
        test_data = valid_spotify_data.copy()
        test_data['track_number'] = value
        with pytest.raises(TypeError, match='track_number'):
            Spotify_Data(**test_data)




    


    

    
    




