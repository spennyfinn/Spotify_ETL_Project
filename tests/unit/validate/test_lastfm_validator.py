import pytest
from src.validate.lastfm_validator import LastFmData
from tests.unit.constants import (
    INVALID_ID_IDS, INVALID_IDS, NO_DOMAIN_URL_VALUES, NO_DOMAIN_URL_VALUES_IDS, VALID_BOOLEAN_VALUES,
    VALID_ID_VALUES, VALID_ID_VALUES_IDS, VALID_URL_VALUES, WRONG_BOOLEAN_TYPES, WRONG_BOOLEAN_TYPES_IDS,
    WRONG_FLOAT_TYPE, WRONG_FLOAT_TYPE_IDS, WRONG_INT_TYPE, WRONG_INT_TYPE_IDS,
    WRONG_STRING_TYPE, WRONG_STRING_TYPE_IDS, EMPTY_STRINGS, EMPTY_STRINGS_IDS,
    VALID_SONG_NAMES, VALID_SONG_NAMES_IDS, VALID_ARTIST_NAMES, VALID_ARTIST_NAMES_IDS, VALID_MBID_VALUES, VALID_MBID_VALUES_IDS,
    INVALID_MBID_VALUES, INVALID_MBID_VALUES_IDS, INVALID_ENGAGEMENT_RATIO_VALUES,
    INVALID_ENGAGEMENT_RATIO_VALUES_IDS, INVALID_PLAYS_PER_LISTENER_VALUES,
    INVALID_PLAYS_PER_LISTENER_VALUES_IDS, INVALID_NEGATIVE_INT_VALUES,
    INVALID_NEGATIVE_INT_VALUES_IDS, VALID_CALCULATED_FIELD_VALUES,
    VALID_CALCULATED_FIELD_VALUES_IDS, VALID_SONG_LISTENERS_VALUES,
    VALID_SONG_LISTENERS_VALUES_IDS, INVALID_CALCULATED_FIELD_VALUES,
    INVALID_CALCULATED_FIELD_VALUES_IDS,VALID_URL_VALUES_IDS
)




class TestLastFmData():
    
    #SONG_NAME
    @pytest.mark.parametrize('value', VALID_SONG_NAMES, ids=VALID_SONG_NAMES_IDS)
    def test_valid_song_names(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['song_name'] = value
        validated_data = LastFmData(**test_data)
        assert validated_data.song_name == 'test song'

    
    @pytest.mark.parametrize('value', EMPTY_STRINGS, ids=EMPTY_STRINGS_IDS)
    def test_invalid_song_names(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['song_name'] = value
        with pytest.raises(ValueError, match='song_name'):
            LastFmData(**test_data)
            

    @pytest.mark.parametrize('value', WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS )
    def test_invalid_types_song_names(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['song_name'] = value
        with pytest.raises(TypeError, match='song_name'):
            LastFmData(**test_data)

    #ARTIST NAME
    @pytest.mark.parametrize('value', VALID_ARTIST_NAMES, ids=VALID_ARTIST_NAMES_IDS)
    def test_valid_artist_names(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['artist_name'] = value
        validated_data = LastFmData(**test_data)
        assert validated_data.artist_name == 'test artist'

    @pytest.mark.parametrize('value', EMPTY_STRINGS, ids=EMPTY_STRINGS_IDS)
    def test_invalid_artist_names(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['artist_name'] = value
        with pytest.raises(ValueError, match='artist_name'):
            LastFmData(**test_data)

    @pytest.mark.parametrize('value', WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_invalid_types_artist_names(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['artist_name'] = value
        with pytest.raises(TypeError, match='artist_name'):
            LastFmData(**test_data)


    #SONG_ID
    @pytest.mark.parametrize('value', VALID_ID_VALUES, ids=VALID_ID_VALUES_IDS)
    def test_valid_song_ids(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['song_id'] = value
        validated_data = LastFmData(**test_data)
        assert validated_data.song_id.strip() == value

    @pytest.mark.parametrize('value', INVALID_IDS, ids=INVALID_ID_IDS)
    def test_invalid_song_ids(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['song_id'] = value
        with pytest.raises(ValueError, match='song_id'):
            LastFmData(**test_data)

    @pytest.mark.parametrize('value', WRONG_STRING_TYPE,ids=WRONG_STRING_TYPE_IDS)
    def test_invalid_types_song_ids(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['song_id'] = value
        with pytest.raises(TypeError, match='song_id'):
            LastFmData(**test_data)

    
    #ARTIST IDS
    @pytest.mark.parametrize('value', VALID_ID_VALUES, ids=VALID_ID_VALUES_IDS)
    def test_valid_artist_ids(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['artist_id'] = value
        validated_data = LastFmData(**test_data)
        assert validated_data.artist_id.strip() == value

    @pytest.mark.parametrize('value', INVALID_IDS, ids=INVALID_ID_IDS)
    def test_invalid_artist_ids(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['artist_id'] = value
        with pytest.raises(ValueError, match='artist_id'):
            LastFmData(**test_data)

    @pytest.mark.parametrize('value', WRONG_STRING_TYPE,ids=WRONG_STRING_TYPE_IDS)
    def test_invalid_types_artist_ids(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['artist_id'] = value
        with pytest.raises(TypeError, match='artist_id'):
            LastFmData(**test_data)

    #MBID
    @pytest.mark.parametrize('value', VALID_MBID_VALUES, ids=VALID_MBID_VALUES_IDS)
    def test_valid_mbid(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['mbid'] = value
        validated_data = LastFmData(**test_data)
        assert validated_data.mbid.strip() == value

    @pytest.mark.parametrize('value', INVALID_MBID_VALUES, ids=INVALID_MBID_VALUES_IDS)
    def test_invalid_mbid(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['mbid'] = value
        with pytest.raises(ValueError, match='mbid'):
            LastFmData(**test_data)

    @pytest.mark.parametrize('value', WRONG_STRING_TYPE[:-1],ids=WRONG_STRING_TYPE_IDS[:-1])
    def test_invalid_types_mbid(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['mbid'] = value
        with pytest.raises(TypeError, match='mbid'):
            LastFmData(**test_data)

    @pytest.mark.parametrize('value', [None],ids=['None'])
    def test_invalid_types_mbid(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['mbid'] = value
        assert test_data['mbid']== None


    #ON TOUR
    @pytest.mark.parametrize('value', VALID_BOOLEAN_VALUES, ids=VALID_BOOLEAN_VALUES)
    def test_valid_on_tour(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['on_tour'] = value
        validated_data = LastFmData(**test_data)
        assert validated_data.on_tour == value

    @pytest.mark.parametrize('value',WRONG_BOOLEAN_TYPES, ids=WRONG_BOOLEAN_TYPES_IDS )
    def test_invalid_types_on_tour(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['on_tour'] = value
        with pytest.raises(TypeError, match='True or False'):
            LastFmData(**test_data)
    
    #ENGAGEMENT RATIO
    @pytest.mark.parametrize('value_ppl,value_total_listeners,value_total_playcount,value_er,value_song_listeners', VALID_CALCULATED_FIELD_VALUES, ids=VALID_CALCULATED_FIELD_VALUES_IDS)
    def test_valid_er(self, lastfm_data, value_ppl, value_total_listeners, value_total_playcount, value_er, value_song_listeners):
        test_data = lastfm_data.copy()
        test_data['artist_total_playcount'] = value_total_playcount
        test_data['artist_total_listeners'] = value_total_listeners
        test_data['plays_per_listener'] = value_ppl
        test_data['num_song_listeners'] = value_song_listeners
        test_data['engagement_ratio'] = value_er
        validated_data = LastFmData(**test_data)
        assert validated_data.engagement_ratio == value_er

    @pytest.mark.parametrize('value', INVALID_ENGAGEMENT_RATIO_VALUES, ids=INVALID_ENGAGEMENT_RATIO_VALUES_IDS)
    def test_invalid_er(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['engagement_ratio'] = value
        with pytest.raises(ValueError, match='engagement_ratio'):
            LastFmData(**test_data)

    @pytest.mark.parametrize('value',WRONG_FLOAT_TYPE, ids=WRONG_FLOAT_TYPE_IDS)
    def test_invalid_types_er(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['engagement_ratio'] = value
        with pytest.raises(TypeError, match='engagement_ratio'):
            LastFmData(**test_data)

    #PLAYS PER LISTENER
    @pytest.mark.parametrize('value_ppl,value_total_listeners,value_total_playcount,value_er,value_song_listeners', VALID_CALCULATED_FIELD_VALUES, ids=VALID_CALCULATED_FIELD_VALUES_IDS)
    def test_valid_ppl(self, lastfm_data, value_ppl, value_total_listeners, value_total_playcount, value_er, value_song_listeners):
        test_data = lastfm_data.copy()
        test_data['artist_total_playcount'] = value_total_playcount
        test_data['artist_total_listeners'] = value_total_listeners
        test_data['plays_per_listener'] = value_ppl
        test_data['engagement_ratio'] = value_er
        test_data['num_song_listeners'] = value_song_listeners
        validated_data = LastFmData(**test_data)
        assert validated_data.plays_per_listener == value_ppl

    @pytest.mark.parametrize('value', INVALID_PLAYS_PER_LISTENER_VALUES, ids=INVALID_PLAYS_PER_LISTENER_VALUES_IDS)
    def test_invalid_ppl(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['plays_per_listener'] = value
        with pytest.raises(ValueError, match='plays_per_listener'):
            LastFmData(**test_data)

    @pytest.mark.parametrize('value', WRONG_FLOAT_TYPE[:-1], ids=WRONG_FLOAT_TYPE_IDS[:-1])
    def test_invalid_types_ppl(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['plays_per_listener'] = value
        with pytest.raises(TypeError, match='plays_per_listener'):
            LastFmData(**test_data)

    def test_return_zero_ppl(self, lastfm_data):
        test_data = lastfm_data.copy()
        test_data['plays_per_listener'] = None
        validated_data = LastFmData(**test_data)
        assert validated_data.plays_per_listener == None

    #NUM SONG LISTENERS
    @pytest.mark.parametrize('value_ppl,value_total_listeners,value_total_playcount,value_er,value_song_listeners', VALID_SONG_LISTENERS_VALUES, ids=VALID_SONG_LISTENERS_VALUES_IDS)
    def test_valid_song_listeners(self, lastfm_data, value_ppl, value_total_listeners, value_total_playcount, value_er, value_song_listeners):
        test_data = lastfm_data.copy()
        test_data['artist_total_playcount'] = value_total_playcount
        test_data['artist_total_listeners'] = value_total_listeners
        test_data['plays_per_listener'] = value_ppl
        test_data['engagement_ratio'] = value_er
        test_data['num_song_listeners'] = value_song_listeners
        validated_data = LastFmData(**test_data)
        assert validated_data.num_song_listeners == value_song_listeners

    @pytest.mark.parametrize('value', INVALID_NEGATIVE_INT_VALUES, ids=INVALID_NEGATIVE_INT_VALUES_IDS)
    def test_invalid_song_listeners(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['num_song_listeners'] = value
        with pytest.raises(ValueError, match='num_song_listeners'):
            LastFmData(**test_data)

    @pytest.mark.parametrize('value', WRONG_INT_TYPE, ids= WRONG_INT_TYPE_IDS)
    def test_invalid_types_song_listeners(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['num_song_listeners'] = value
        with pytest.raises(TypeError, match='num_song_listeners'):
            LastFmData(**test_data)

    #ARTIST TOTAL PLAYCOUNT
    @pytest.mark.parametrize('value_ppl,value_total_listeners,value_total_playcount,value_er,value_song_listeners', VALID_SONG_LISTENERS_VALUES, ids=VALID_SONG_LISTENERS_VALUES_IDS)
    def test_valid_artist_total_playcount(self, lastfm_data, value_ppl, value_total_listeners, value_total_playcount, value_er, value_song_listeners):
        test_data = lastfm_data.copy()
        test_data['artist_total_playcount'] = value_total_playcount
        test_data['artist_total_listeners'] = value_total_listeners
        test_data['plays_per_listener'] = value_ppl
        test_data['engagement_ratio'] = value_er
        test_data['num_song_listeners'] = value_song_listeners
        validated_data = LastFmData(**test_data)
        assert validated_data.artist_total_playcount == value_total_playcount

    @pytest.mark.parametrize('value', INVALID_NEGATIVE_INT_VALUES, ids=INVALID_NEGATIVE_INT_VALUES_IDS)
    def test_invalid_artist_total_playcount(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['artist_total_playcount'] = value
        with pytest.raises(ValueError, match='artist_total_playcount'):
            LastFmData(**test_data)

    @pytest.mark.parametrize('value', WRONG_INT_TYPE, ids=WRONG_INT_TYPE_IDS)
    def test_invalid_types_artist_total_playcount(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['artist_total_playcount'] = value
        with pytest.raises(TypeError, match='artist_total_playcount'):
            LastFmData(**test_data)

    #ARTIST TOTAL LISTENERS
    @pytest.mark.parametrize('value_ppl,value_total_listeners,value_total_playcount,value_er,value_song_listeners', VALID_SONG_LISTENERS_VALUES, ids=VALID_SONG_LISTENERS_VALUES_IDS)
    def test_valid_artist_total_listeners(self, lastfm_data, value_ppl, value_total_listeners, value_total_playcount, value_er, value_song_listeners):
        test_data = lastfm_data.copy()
        test_data['artist_total_playcount'] = value_total_playcount
        test_data['artist_total_listeners'] = value_total_listeners
        test_data['plays_per_listener'] = value_ppl
        test_data['engagement_ratio'] = value_er
        test_data['num_song_listeners'] = value_song_listeners
        validated_data = LastFmData(**test_data)
        assert validated_data.artist_total_listeners == value_total_listeners

    @pytest.mark.parametrize('value', INVALID_NEGATIVE_INT_VALUES, ids=INVALID_NEGATIVE_INT_VALUES_IDS)
    def test_invalid_artist_total_listeners(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['artist_total_listeners'] = value
        with pytest.raises(ValueError, match='artist_total_listeners'):
            LastFmData(**test_data)

    @pytest.mark.parametrize('value', WRONG_INT_TYPE, ids=WRONG_INT_TYPE_IDS)
    def test_invalid_types_artist_total_listeners(self, lastfm_data, value):
        test_data = lastfm_data.copy()
        test_data['artist_total_listeners'] = value
        with pytest.raises(TypeError, match='artist_total_listeners'):
            LastFmData(**test_data)

    #CALCULATED VALUES
    @pytest.mark.parametrize('ppl,listeners,playcount,er,song_listeners', VALID_CALCULATED_FIELD_VALUES, ids=VALID_CALCULATED_FIELD_VALUES_IDS)
    def test_valid_calculated_fields(self, lastfm_data, listeners, playcount, song_listeners, ppl, er):
        test_data = lastfm_data.copy()
        test_data['artist_total_playcount'] = playcount
        test_data['artist_total_listeners'] = listeners
        test_data['plays_per_listener'] = ppl
        test_data['engagement_ratio'] = er
        test_data['num_song_listeners'] = song_listeners

        validated_data = LastFmData(**test_data)
        assert validated_data.engagement_ratio == er
        assert validated_data.plays_per_listener == ppl

    @pytest.mark.parametrize('ppl,listeners,playcount,er,song_listeners', INVALID_CALCULATED_FIELD_VALUES, ids=INVALID_CALCULATED_FIELD_VALUES_IDS)
    def test_invalid_calculated_fields(self, lastfm_data, ppl, listeners, playcount, er, song_listeners):
        test_data = lastfm_data.copy()
        test_data['artist_total_playcount'] = playcount
        test_data['artist_total_listeners'] = listeners
        test_data['plays_per_listener'] = ppl
        test_data['engagement_ratio'] = er
        test_data['num_song_listeners'] = song_listeners

        with pytest.raises(ValueError, match="calculation"):
            LastFmData(**test_data)

    
