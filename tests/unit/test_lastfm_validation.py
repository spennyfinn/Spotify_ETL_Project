import pytest
from src.validation.lastfm import LastFm




class TestLastFm():

    @pytest.fixture
    def data(self):
        return{
        'song_name': 'Test Song ',
        'artist_name': 'Test Artist',
        'num_song_listeners': 80000,
        'song_url': 'https://song_url.com',
        'mbid': '12345678-abc3-4d4c-0b90-0987654321ab',
        'on_tour': False,
        'song_id': '21lop6789fyt385Yt890ab',
        'artist_total_playcount': 900000,
        'artist_total_listeners': 800000,
        'plays_per_listener': 120.9,
        'engagement_ratio':.10,
        'artist_id': '1Er4567890BOutf6789012'
        }
    
    
    #SONG_NAME
    def test_valid_song_names(self, data):
        for value in ['test song', 'Test Song', 'TEST SONG', ' Test Song ']:
            data['song_name']= value
            validated_data=LastFm(**data)
            assert validated_data.song_name=='test song'

    
    def test_invalid_song_names(self, data):
        for value in ['', '  ', '       ']:
            data['song_name']= value
            with pytest.raises(ValueError, match='song_name'):
                LastFm(**data)
            

    def test_invalid_types_song_names(self, data):
        for value in [False, 0, 1.9, [], {}]:
            data['song_name']= value
            with pytest.raises(TypeError, match='song_name'):
                LastFm(**data)

    #ARTIST NAME
    def test_valid_artist_names(self, data):
        for value in ['test artist', 'Test Artist', 'TEST ARTIST', ' Test Artist ']:
            data['artist_name']= value
            validated_data=LastFm(**data)
            assert validated_data.artist_name=='test artist'

    def test_invalid_artist_names(self, data):
        for value in ['', '  ', '       ']:
            data['artist_name']= value
            with pytest.raises(ValueError, match='artist_name'):
                LastFm(**data)

    def test_invalid_types_artist_names(self, data):
        for value in [False, 0, 1.9, [], {}, None]:
            data['artist_name']= value
            with pytest.raises(TypeError, match='artist_name'):
                LastFm(**data)


    #SONG_ID
    def test_valid_song_ids(self, data):
        for value in ['12345678901234567890ab', '09876543210987654321db', 'abcdef123456abcdef1234']:
            data['song_id']= value
            validated_data=LastFm(**data)
            assert validated_data.song_id.strip()==value

    def test_invalid_song_ids(self, data):
        for value in [' ', '1234567812*(567890', '123456789012#4567890abc', 'qw@@rtyuiopasdfghjklzx1']:
            data['song_id']= value
            with pytest.raises(ValueError, match='song_id'):
                LastFm(**data)

    def test_invalid_types_song_ids(self, data):
        for value in [False, 0, 1.9, [], {}, None]:
            data['song_id']= value
            with pytest.raises(TypeError, match='song_id'):
                LastFm(**data)

    
    #ARTIST IDS
    def test_valid_artist_ids(self, data):
        for value in ['12345678901234567890ab', '09876543210987654321db', 'abcdef123456abcdef1234']:
            data['artist_id']= value
            validated_data=LastFm(**data)
            assert validated_data.artist_id.strip()==value

    def test_invalid_artist_ids(self, data):
        for value in [' ', '1234567812*(567890', '123456789012#4567890abc', 'qw@@rtyuiopasdfghjklzx1']:
            data['artist_id']= value
            with pytest.raises(ValueError, match='artist_id'):
                LastFm(**data)

    def test_invalid_types_artist_ids(self, data):
        for value in [False, 0, 1.9, [], {}, None]:
            data['artist_id']= value
            with pytest.raises(TypeError, match='artist_id'):
                LastFm(**data)

    #SONG URL
    def test_valid_song_url(self, data):
        for value in ['https://song.com', 'http://hello+from+the+other+side.com', 'https://s']:
            data['song_url']= value
            validated_data=LastFm(**data)
            assert validated_data.song_url.strip()==value

    def test_invalid_song_url(self, data):
        for value in ['',' ', 'htt://music.com', 'HTTPS://hello.com', 'http//', 'http:/']:
            data['song_url']= value
            with pytest.raises(ValueError, match='song_url'):
                LastFm(**data)

    def test_invalid_types_song_url(self, data):
        for value in [False, 0, 1.9, [], {}, None]:
            data['song_url']= value
            with pytest.raises(TypeError, match='song_url'):
                LastFm(**data)

    #MBID
    def test_valid_mbid(self, data):
        for value in ['12345678-1234-1234-1234-123456789012', '123bc678-bcda-feda-12bc-123456bb0122']:
            data['mbid']= value
            validated_data=LastFm(**data)
            assert validated_data.mbid.strip()==value

    def test_invalid_mbid(self, data):
        for value in ['',' ', '12345678-1234-1234-1234-12345678901', '12345678-1234-1234-123a4-123456789012', '1234@678-1234-1234-1234-123456789012', '12345678-1234-1234-1234-1234567890g2', '12345678-1234-1234-1234123456789012']:
            data['mbid']= value
            with pytest.raises(ValueError, match='mbid'):
                LastFm(**data)

    def test_invalid_types_mbid(self, data):
        for value in [False, 0, 1.9, [], {}, None]:
            data['mbid']= value
            with pytest.raises(TypeError, match='mbid'):
                LastFm(**data)

    #ON TOUR
    def test_valid_on_tour(self, data):
        for value in [True, False]:
            data['on_tour']=value
            validated_data= LastFm(**data)
            assert validated_data.on_tour==value

    def test_invalid_types_mbid(self, data):
        for value in ['False', 0, 1.9, [], {}, None]:
            data['on_tour']= value
            with pytest.raises(TypeError, match='on_tour'):
                LastFm(**data)
    
    #ENGAGEMENT RATIO
    def test_valid_er(self, data):
        for value in [1.0, 0.0, .5, .25, .75]:
            data['engagement_ratio']= value
            validated_data=LastFm(**data)
            assert validated_data.engagement_ratio==value

    def test_invalid_er(self, data):
        for value in [-1.0, 1.001, 100.1, -100.1]:
            data['engagement_ratio']= value
            with pytest.raises(ValueError, match='engagement_ratio'):
                LastFm(**data)

    def test_invalid_types_er(self, data):
        for value in [False, 0, '1.9', [], {}, None]:
            data['engagement_ratio']= value
            with pytest.raises(TypeError, match='engagement_ratio'):
                LastFm(**data)

    #PLAYS PER LISTENER
    def test_valid_ppl(self, data):
        for value in [0.0, 1000.0, 2000.0]:
            data['plays_per_listener']= value
            validated_data=LastFm(**data)
            assert validated_data.plays_per_listener==value

    def test_invalid_ppl(self, data):
        for value in [-.00001, 2000.1, 5000.0, -100.1]:
            data['plays_per_listener']= value
            with pytest.raises(ValueError, match='plays_per_listener'):
                LastFm(**data)

    def test_invalid_types_ppl(self, data):
        for value in [False, 0, '1.9', [], {}]:
            data['plays_per_listener']= value
            with pytest.raises(TypeError, match='plays_per_listener'):
                LastFm(**data)

    def test_return_zero_ppl(self, data):
        data['plays_per_listener']= None
        validated_data=LastFm(**data)
        assert validated_data.plays_per_listener==None

    #NUM SONG LISTENERS
    def test_valid_song_listeners(self, data):
        for value in [0, 1, 100, 10000, 999999999]:
            data['num_song_listeners']= value
            validated_data=LastFm(**data)
            assert validated_data.num_song_listeners==value

    def test_invalid_song_listeners(self, data):
        for value in [-1, -10000]:
            data['num_song_listeners']= value
            with pytest.raises(ValueError, match='num_song_listeners'):
                LastFm(**data)

    def test_invalid_types_song_listeners(self, data):
        for value in [False, 0.0, '1.9', [], {}, None]:
            data['num_song_listeners']= value
            with pytest.raises(TypeError, match='num_song_listeners'):
                LastFm(**data)

    #ARTIST TOTAL PLAYCOUNT
    def test_valid_artist_total_playcount(self, data):
        for value in [0, 1, 100, 10000, 999999999]:
            data['artist_total_playcount']= value
            validated_data=LastFm(**data)
            assert validated_data.artist_total_playcount==value

    def test_invalid_artist_total_playcount(self, data):
        for value in [-1, -10000]:
            data['artist_total_playcount']= value
            with pytest.raises(ValueError, match='artist_total_playcount'):
                LastFm(**data)

    def test_invalid_types_artist_total_playcount(self, data):
        for value in [False, 0.0, '1.9', [], {}, None]:
            data['artist_total_playcount']= value
            with pytest.raises(TypeError, match='artist_total_playcount'):
                LastFm(**data)

    #ARTIST TOTAL LISTENERS
    def test_valid_artist_total_listeners(self, data):
        for value in [0, 1, 100, 10000, 999999999]:
            data['artist_total_listeners']= value
            validated_data=LastFm(**data)
            assert validated_data.artist_total_listeners==value

    def test_invalid_artist_total_listeners(self, data):
        for value in [-1, -10000]:
            data['artist_total_listeners']= value
            with pytest.raises(ValueError, match='artist_total_listeners'):
                LastFm(**data)

    def test_invalid_types_artist_total_listeners(self, data):
        for value in [False, 0.0, '1.9', [], {}, None]:
            data['artist_total_listeners']= value
            with pytest.raises(TypeError, match='artist_total_listeners'):
                LastFm(**data)

    #CALCULATED VALUES
    
