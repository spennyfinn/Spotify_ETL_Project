

import pytest
from src.load.parsers import parse_audio_features_data,parse_lastfm_message,parse_spotify_message
from tests.unit.constants import AUDIO_FEATURES_REQUIRED_FIELDS, LAST_FM_OPTIONAL_FIELDS, LASTFM_REQUIRED_FIELDS, SPOTIFY_OPTIONAL_FIELDS, SPOTIFY_REQUIRED_FIELDS, WRONG_DICT_TYPES, WRONG_DICT_TYPES_IDS
class TestParsers:    


    def test_valid_spotify(self, valid_spotify_data):
        '''Tests valid spotify data against the parse_spotify_message() function'''
        song, album , artist= parse_spotify_message(valid_spotify_data)
        assert song[0]=='test song'
        assert song[1]== 'wer45poiup1234567nnpp2'
        assert song[2]== 600000
        assert song[3]== 600
        assert song[4]== 10.0
        assert song[5]== '2023-02-02'
        assert song[6]== 'day'
        assert song[7]== True
        assert song[8]== 70
        assert song[9]== 3
        assert song[10]== '1io456789012aer6789012'
        assert song[11] == '1234567890abcdefghijk1'

        assert album[0]=='test album'
        assert album[1]== 'wer45poiup1234567nnpp2'
        assert album[2]== 'single'
        assert album[3]== 99
        assert album[4]== '1234567890abcdefghijk1'
        
        assert artist[0]=='wer45poiup1234567nnpp2'
        assert artist[1]== 'test artist'

    @pytest.mark.parametrize('value', SPOTIFY_OPTIONAL_FIELDS)
    def test_missing_fields_spotify(self, valid_spotify_data, value):
        '''Tests invalid spotify data (missing non-required fields) against the parse_spotify_message() function'''
        missing_data={}
        for k, v in valid_spotify_data.items():
            if k!=value:
                missing_data[k]=v
        with pytest.raises(ValueError, match='There was invalid data'):
            parse_spotify_message(missing_data)

    @pytest.mark.parametrize('req_field', SPOTIFY_REQUIRED_FIELDS)
    def test_missing_req_fields_spotify(self, valid_spotify_data, req_field):
        '''Tests invalid spotify data (missing required fields) against the parse_spotify_message() function'''
        missing_data_dict={}
        for key, value in valid_spotify_data.items():
            if key != req_field:
                missing_data_dict[key]=value
        with pytest.raises(ValueError, match =req_field):
            parse_spotify_message(missing_data_dict)

    @pytest.mark.parametrize('req_field', SPOTIFY_REQUIRED_FIELDS)
    def test_req_fields_none_spotify(self, valid_spotify_data, req_field):
        '''Tests invalid spotify data (required fields = None) against the parse_spotify_message() function'''
        data= valid_spotify_data.copy()
        data[req_field]=None

        with pytest.raises(ValueError, match=req_field):
            parse_spotify_message(data)


    @pytest.mark.parametrize('wrong_type', WRONG_DICT_TYPES, ids=WRONG_DICT_TYPES_IDS )
    def test_wrong_type_spotify(self, wrong_type):
        with pytest.raises(TypeError, match='data should be a dictionary'):
            parse_spotify_message(wrong_type)

    
    

    def test_valid_lastfm(self, valid_lastfm_data): 
        """Tests valid lastfm data against the parse_last_fm() function"""
        song,artist= parse_lastfm_message(valid_lastfm_data)
        assert song[0]=='test song'
        assert song[1]== '21lop6789fyt385Yt890ab'
        assert song[2]== 50000
        assert song[3]== '1Er4567890BOutf6789012'
        assert song[4]== '12345678-abc3-4d4c-0b90-0987654321ab'
        assert song[5]== .25

        assert artist[0]=='test artist'
        assert artist[1]== '1Er4567890BOutf6789012'
        assert artist[2]== False
        assert artist[3]== 200000
        assert artist[4]== 100000
        assert artist[5]== .5

    def test_wrong_fields_lastfm(self):
        '''Makes sure the parser catches wrong field names like on_tours instead of on_tour'''
        input_data= {
            'song_name': 'test song',
            'artist_name': 'test artist',
            'artist_id': '1234567890123456789012',
            'num_song_listeners': 10000,
            'mbid': '12345678-1234-1234-1234-123456789012',
            'song_url': 'https://url.com',
            'on_tours': False,
            'artist_total_listeners': 80000,
            'artist_total_playcount': 900000,
            'song_id': '123456789008765432112',
            'engagement_ratio': .7,
            'plays_per_listener': .3,
            'source': 'Lastfm'
        }
        with pytest.raises((ValueError), match='on_tour'):
            parse_lastfm_message(input_data)

    @pytest.mark.parametrize('req_field', LASTFM_REQUIRED_FIELDS)
    def test_req_fields_none_lastfm(self, valid_lastfm_data, req_field):
        '''Tests invalid lastfm data (required fields = None) against the parse_lastfm_message() function'''
        data = valid_lastfm_data.copy()
        data[req_field]=None
        with pytest.raises(ValueError, match =req_field):
            parse_lastfm_message(data)

    @pytest.mark.parametrize('req_field', LASTFM_REQUIRED_FIELDS)
    def test_missing_req_fields_lastfm(self, valid_lastfm_data, req_field):
        '''Tests invalid lastfm data (missing required fields) against the parse_lastfm_message() function'''
        missing_data_dict={}
        for key, value in valid_lastfm_data.items():
            if key != req_field:
                missing_data_dict[key]=value
        with pytest.raises(ValueError, match =req_field):
            parse_lastfm_message(missing_data_dict)

    @pytest.mark.parametrize('value', LAST_FM_OPTIONAL_FIELDS)
    def test_missing_optional_fields_lastfm(self, valid_lastfm_data, value):
        '''Tests invalid lastfm data (missing optional fields) against the parse_lastfm_message() function'''
        missing_data_dict={}
        for k, v in valid_lastfm_data.items():
            if k!=value:
                missing_data_dict[k]=v
        with pytest.raises(ValueError, match =value):
            parse_lastfm_message(missing_data_dict)

    
    @pytest.mark.parametrize('wrong_type', WRONG_DICT_TYPES, ids=WRONG_DICT_TYPES_IDS)
    def test_wrong_type_lastfm(self, wrong_type):
        '''Verifies parser rejects non-dict inputs like strings, numbers, etc'''
        with pytest.raises(TypeError, match='dictionary'):
            parse_lastfm_message(wrong_type)
        


    #AUDIO FEATURES TESTS
    def test_valid_audio_features(self,valid_audio_features):
        '''Tests valid audio features data against the parse_audio_features_data() function'''
        output= parse_audio_features_data(valid_audio_features)
        assert output[0]=='1gj856fdB53pL96DStrn08'  # song_id
        assert output[1]== 60.2  # bpm
        assert output[2]== .93  # energy
        assert output[3]== 500.2  # spectral_centroid
        assert output[4]== 0.5  # zero_crossing_rate
        assert output[5]== .6553  # danceability
        assert output[6]== 'https://audio_features.com'  # preview_url
        assert output[7]== .5  # harmonic_ratio
        assert output[8]== .5  # percussive_ratio

    @pytest.mark.parametrize('field', AUDIO_FEATURES_REQUIRED_FIELDS)
    def test_missing_req_fields_audio_features(self, valid_audio_features, field):
        '''Tests invalid audio features data (missing required fields) against the parse_audio_features_data() function'''
        data={k: v for k,v in valid_audio_features.items() if k != field}
        with pytest.raises(ValueError, match=field):
            parse_audio_features_data(data)

        
    @pytest.mark.parametrize('field', AUDIO_FEATURES_REQUIRED_FIELDS)
    def test_req_fields_none_audio_features(self, valid_audio_features, field):
        '''Tests invalid audio features data (required fields = None) against the parse_audio_features_data() function'''
        data=valid_audio_features.copy()
        data[field]=None
        with pytest.raises(ValueError, match=field):
            parse_audio_features_data(data)
            

    @pytest.mark.parametrize('wrong_type', WRONG_DICT_TYPES, ids=WRONG_DICT_TYPES_IDS)
    def test_wrong_type_audio_features(self, wrong_type):
        '''Tests invalid audio features data (wrong dtypes) against the parse_audio_features_data() function'''
        with pytest.raises(TypeError, match='Input data should be a dict'):
            parse_audio_features_data(wrong_type)
         