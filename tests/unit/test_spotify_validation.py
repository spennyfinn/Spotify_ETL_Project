
import pytest
from src.validation.spotify import Spotify_Data

class TestSpotifyValidation:

    @pytest.fixture
    def valid_spotify_data(self)-> dict:
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

    #POPULARITY
    def test_popularity_boundaries(self, valid_spotify_data):
        valid_nums = [70, 50,0,100]
        for nums in valid_nums:
            valid_spotify_data['popularity']=nums
            data=Spotify_Data(**valid_spotify_data)
            assert data.popularity==nums

    def test_popularity_out_of_range(self, valid_spotify_data):
        for invalid_num in [-1,-100,101,150]:
            valid_spotify_data['popularity']= invalid_num
            with pytest.raises(ValueError, match='popularity'):
                Spotify_Data(**valid_spotify_data)
    
    def test_popularity_wrong_types(self, valid_spotify_data):
        for type in ['20', False, 20.7, [], None, {}]:
            valid_spotify_data['popularity']=type
            with pytest.raises(TypeError, match='popularity'):
                Spotify_Data(**valid_spotify_data)

    #SONG NAME
    def test_valid_song_names(self, valid_spotify_data):
        data=Spotify_Data(**valid_spotify_data)
        assert data.song_name.lower().strip()== 'test song'

    def test_invalid_strings_song_names(self,valid_spotify_data):
        for value in ['', '  ', '      ']:
            valid_spotify_data['song_name']=value
            with pytest.raises(ValueError, match='song_name'):
                Spotify_Data(**valid_spotify_data)

    def test_invalid_types_song_names(self, valid_spotify_data):
        for value in [0, 0.1, {}, None, [], False]:
            valid_spotify_data['album_title']=value
            with pytest.raises(TypeError, match='album_title'):
                Spotify_Data(**valid_spotify_data)

    #ARTIST NAMES:
    def test_valid_artist_names(self, valid_spotify_data):
        data=Spotify_Data(**valid_spotify_data)
        assert data.artist_name.lower().strip()== 'test artist'

    def test_invalid_strings_artist_names(self,valid_spotify_data):
        for value in ['', '  ', '      ']:
            valid_spotify_data['artist_name']=value
            with pytest.raises(ValueError, match='artist_name'):
                Spotify_Data(**valid_spotify_data)

    def test_invalid_types_artist_names(self, valid_spotify_data):
        for value in [0, 0.1, {}, None, [], False]:
            valid_spotify_data['artist_name']=value
            with pytest.raises(TypeError, match='artist_name'):
                Spotify_Data(**valid_spotify_data)


    #ALBUM TITLE
    def test_valid_album_titles(self, valid_spotify_data):
        data=Spotify_Data(**valid_spotify_data)
        assert data.album_title.lower().strip()=='test album'

    def test_invalid_strings_album_title(self,valid_spotify_data):
        for value in ['', '  ', '      ']:
            valid_spotify_data['album_title']=value
            with pytest.raises(ValueError, match='album_title'):
                Spotify_Data(**valid_spotify_data)

    def test_invalid_types_album_title(self, valid_spotify_data):
        for value in [0, 0.1, {}, None, [], False]:
            valid_spotify_data['album_title']=value
            with pytest.raises(TypeError, match='album_title'):
                Spotify_Data(**valid_spotify_data)

    


    #IDS
    def test_valid_ids(self, valid_spotify_data):
        data = Spotify_Data(**valid_spotify_data)

        assert data.album_id == valid_spotify_data['album_id']
        assert data.song_id == valid_spotify_data['song_id'] 
        assert data.artist_id == valid_spotify_data['artist_id']

    #ARTIST IDS
    def test_invalid_inputs_artist_ids(self,valid_spotify_data):
        for value in ['', '  ', valid_spotify_data['artist_id']+'ii' ,valid_spotify_data['artist_id'][:21], 'a', '123456789012345678901@' ]:
            valid_spotify_data['artist_id']=value
            with pytest.raises(ValueError, match='artist_id'):
                Spotify_Data(**valid_spotify_data)

    def test_invalid_types_artist_ids(self, valid_spotify_data):
        for value in [0, 0.1, {}, None, [], False]:
            valid_spotify_data['album_id']=value
            with pytest.raises(TypeError, match='album_id'):
                Spotify_Data(**valid_spotify_data)
    
    
    #SONG IDS
    def test_invalid_inputs_song_ids(self,valid_spotify_data):
        for value in ['', '  ', valid_spotify_data['artist_id']+'ii' ,valid_spotify_data['artist_id'][:21], 'a', '123456789012345678901@' ]:
            valid_spotify_data['song_id']=value
            with pytest.raises(ValueError, match='song_id'):
                Spotify_Data(**valid_spotify_data)
                
    def test_invalid_types_song_ids(self, valid_spotify_data):
        for value in [0, 0.1, {}, None, [], False]:
            valid_spotify_data['song_id']=value
            with pytest.raises(TypeError, match='song_id'):
                Spotify_Data(**valid_spotify_data)


    #ALBUM IDS
    def test_invalid_inputs_album_ids(self,valid_spotify_data):
        for value in ['', '  ', valid_spotify_data['album_id']+'ii' ,valid_spotify_data['album_id'][:21], 'a', '123456789012345678901@' ]:
            valid_spotify_data['album_id']=value
            with pytest.raises(ValueError, match='album_id'):
                Spotify_Data(**valid_spotify_data)
                
    def test_invalid_types_album_ids(self, valid_spotify_data):
        for value in [0, 0.1, {}, None, [], False]:
            valid_spotify_data['album_id']=value
            with pytest.raises(TypeError, match='album_id'):
                Spotify_Data(**valid_spotify_data)

    #DURATION MS
    def test_valid_duration_ms(self, valid_spotify_data):
        for value_sec, value_ms, value_min in [(1, 1000, .02) , (7200, 7200000, 120.0), (200, 200000, 3.33)]:
            valid_spotify_data['duration_minutes']= value_min
            valid_spotify_data['duration_ms']=value_ms
            valid_spotify_data['duration_seconds']=value_sec
            data = Spotify_Data(**valid_spotify_data)
            assert data.duration_ms == value_ms
        

    def test_invalid_inputs_duration_ms(self,valid_spotify_data):
        for value in [999, 7200001, 10000000, -100, 0]:
            valid_spotify_data['duration_ms']=value
            with pytest.raises(ValueError, match='duration_ms'):
                Spotify_Data(**valid_spotify_data)
                
    def test_invalid_types_duration_ms(self, valid_spotify_data):
        for value in ['20',-1.90, None, {}, False, []]:
            valid_spotify_data['duration_ms']=value
            with pytest.raises(TypeError, match='duration_ms'):
                Spotify_Data(**valid_spotify_data)


    #DURATION SECONDS
    def test_valid_duration_seconds(self, valid_spotify_data):
        for value_sec, value_ms, value_min in [(1, 1000, .02) , (7200, 7200000, 120.0), (200, 200000, 3.33)]:
            valid_spotify_data['duration_minutes']= value_min
            valid_spotify_data['duration_ms']=value_ms
            valid_spotify_data['duration_seconds']=value_sec
            data = Spotify_Data(**valid_spotify_data)
            assert data.duration_seconds == value_sec
        

    def test_invalid_inputs_duration_seconds(self,valid_spotify_data):
        for value in [ 7200, 10000, -100, 0]:
            valid_spotify_data['duration_seconds']=value
            with pytest.raises(ValueError, match='duration_seconds'):
                Spotify_Data(**valid_spotify_data)
                
    def test_invalid_types_duration_seconds(self, valid_spotify_data):
        for value in ['20',-1.90, None, {}, False, []]:
            valid_spotify_data['duration_seconds']=value
            with pytest.raises(TypeError, match='duration_seconds'):
                Spotify_Data(**valid_spotify_data)

    #DURATION MINUTES
    def test_valid_duration_minutes(self, valid_spotify_data):
        for value_sec, value_ms, value_min in [(1, 1000, .02) , (7200, 7200000, 120.0), (200, 200000, 3.33)]:
            valid_spotify_data['duration_minutes']= value_min
            valid_spotify_data['duration_ms']=value_ms
            valid_spotify_data['duration_seconds']=value_sec
            data = Spotify_Data(**valid_spotify_data)
            assert data.duration_minutes == value_min
        

    def test_invalid_inputs_duration_minutes(self,valid_spotify_data):
        for value in [ .016, 120.0, -100.0, 0.0, 200.0]:
            valid_spotify_data['duration_minutes']=value
            with pytest.raises(ValueError, match='duration_minutes'):
                Spotify_Data(**valid_spotify_data)
                
    def test_invalid_types_duration_minutes(self, valid_spotify_data):
        for value in ['20',1, None, {}, False, []]:
            valid_spotify_data['duration_minutes']=value
            with pytest.raises(TypeError, match='duration_minutes'):
                Spotify_Data(**valid_spotify_data)

    #MODEL CALCULATIONS:
    def test_duration_inconsistency_validation(self, valid_spotify_data):
        valid_spotify_data['duration_seconds'] = 100
        with pytest.raises(ValueError, match='calculated incorrectly'):
            Spotify_Data(**valid_spotify_data)

     #ALBUM TYPE
    def test_valid_album_type(self, valid_spotify_data):
        for val in ['album', 'single', 'compilation']:
            valid_spotify_data['album_type']=val
            data = Spotify_Data(**valid_spotify_data)
            assert data.album_type == valid_spotify_data['album_type']
        

    def test_invalid_inputs_album_type(self,valid_spotify_data):
        for value in ['albu', '', '   ', 'singler', 'compilation@', '12345']:
            valid_spotify_data['album_type']=value
            with pytest.raises(ValueError, match='album_type'):
                Spotify_Data(**valid_spotify_data)
                
    def test_invalid_types_album_type(self, valid_spotify_data):
        for value in [20,-1.90, None, {}, False, []]:
            valid_spotify_data['album_type']=value
            with pytest.raises(TypeError, match='album_type'):
                Spotify_Data(**valid_spotify_data)

    #RELEASE_DATE_PRECISION
    def test_valid_date_precision(self, valid_spotify_data):
        for val in ['day', 'month', 'year']:
            valid_spotify_data['release_date_precision']=val
            data = Spotify_Data(**valid_spotify_data)
            assert data.release_date_precision == valid_spotify_data['release_date_precision']
        

    def test_invalid_inputs_date_precision(self,valid_spotify_data):
        for value in ['da', 'days', '   ', 'mont', 'month@', '12345', 'Years', "YER"]:
            valid_spotify_data['release_date_precision']=value
            with pytest.raises(ValueError, match='release_date_precision'):
                Spotify_Data(**valid_spotify_data)
                
    def test_invalid_types_date_precision(self, valid_spotify_data):
        for value in [20,-1.90, None, {}, False, []]:
            valid_spotify_data['release_date_precision']=value
            with pytest.raises(TypeError, match='release_date_precision'):
                Spotify_Data(**valid_spotify_data)

    #ALBUM TOTAL TRACKS
    def test_valid_album_total_tracks(self, valid_spotify_data):
        for value in [1,100, 50, 13, 75]:
            valid_spotify_data['album_total_tracks']=value
            data = Spotify_Data(**valid_spotify_data)
            assert data.album_total_tracks == value

    def test_validate_return_zero_album_total_tracks(self,valid_spotify_data):
        for value in [None]:
            valid_spotify_data['album_total_tracks'] = value
            data=Spotify_Data(**valid_spotify_data)
            assert data.album_total_tracks ==0
    

    def test_invalid_inputs_album_total_tracks(self,valid_spotify_data):
        for value in [-1, -50, 101, 200 ]:
            valid_spotify_data['album_total_tracks']=value
            with pytest.raises(ValueError, match='album_total_tracks'):
                Spotify_Data(**valid_spotify_data)
    
    def test_invalid_types_album_total_tracks(self, valid_spotify_data):
        for value in [False, '20', 199.9, [], {}]:
            valid_spotify_data['album_total_tracks']=value
            with pytest.raises(TypeError, match='album_total_tracks'):
                Spotify_Data(**valid_spotify_data)

    #IS PLAYABLE
    def test_valid_is_playable(self, valid_spotify_data):
        for value in [True, False]:
            valid_spotify_data['is_playable']=value
            data = Spotify_Data(**valid_spotify_data)
            assert data.is_playable == value
    
    def test_invalid_types_is_playable(self, valid_spotify_data):
        for value in [46, '20', 199.9, [], {}]:
            valid_spotify_data['is_playable']=value
            with pytest.raises(TypeError, match='is_playable'):
                Spotify_Data(**valid_spotify_data)

    #IS EXPLICIT
    def test_valid_is_explicit(self, valid_spotify_data):
        for value in [True, False]:
            valid_spotify_data['is_explicit']=value
            data = Spotify_Data(**valid_spotify_data)
            assert data.is_explicit == value
    
    def test_invalid_types_is_explcit(self, valid_spotify_data):
        for value in [46, '20', 199.9, [], {}]:
            valid_spotify_data['is_explicit']=value
            with pytest.raises(TypeError, match='is_explicit'):
                Spotify_Data(**valid_spotify_data)

    #TRACK NUMBER
    def test_valid_track_number(self, valid_spotify_data):
        for value in [1,100, 50, 13, 75]:
            valid_spotify_data['track_number']=value
            data = Spotify_Data(**valid_spotify_data)
            assert data.track_number == value
    

    def test_invalid_inputs_track_number(self,valid_spotify_data):
        for value in [-1, -50, 101, 200 ]:
            valid_spotify_data['track_number']=value
            with pytest.raises(ValueError, match='track_number'):
                Spotify_Data(**valid_spotify_data)
    
    def test_invalid_types_track_number(self, valid_spotify_data):
        for value in [False, '20', 199.9, [], {}]:
            valid_spotify_data['track_number']=value
            with pytest.raises(TypeError, match='track_number'):
                Spotify_Data(**valid_spotify_data)




    


    

    
    




