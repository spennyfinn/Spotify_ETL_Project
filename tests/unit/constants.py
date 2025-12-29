import numpy as np
##################################
# BASIC TYPE CONSTANTS 
##################################

EMPTY_STRINGS = ['', ' ', '\t']
EMPTY_STRINGS_IDS = ['Empty String', 'One Space', 'One Tab']

WRONG_STRING_TYPE = [False, 0, 1.9, [], {}, None]
WRONG_STRING_TYPE_IDS = ['Boolean', 'Integer', 'Float', 'Empty List', 'Empty Dict', 'None']

WRONG_INT_TYPE = [False, 1.9, 'string', [], {}, None]
WRONG_INT_TYPE_IDS = ['Boolean', 'Float', 'String', 'Empty List', 'Empty Dict', 'None']

WRONG_FLOAT_TYPE = [False, 1, 'string', [], {}, None]
WRONG_FLOAT_TYPE_IDS = ['Boolean', 'Float', 'String', 'Empty List', 'Empty Dict', 'None']

WRONG_BOOLEAN_TYPES = ['String', 0, 1.9, [], {}, None]
WRONG_BOOLEAN_TYPES_IDS = ['String', 'Integer', 'Float', 'Empty List', 'Empty Dict', 'None']
VALID_BOOLEAN_VALUES = [True, False]

WRONG_DICT_TYPES=['String', 0, 1.9, False, None, []]
WRONG_DICT_TYPES_IDS= ['String', 'Integer', "Float", 'Boolean', 'None', 'Empty List']

WRONG_STRING_PAIRS = [(value, value) for value in WRONG_STRING_TYPE]
WRONG_STRING_PAIRS_IDS = [(f"{value} Pair") for value in WRONG_STRING_TYPE]

#################################
# ID AND URL VALIDATION CONSTANTS
#################################


VALID_ID_VALUES = ['1234567890123456789012', 'qwertyuioplkjhgfdsazxc', 'abcdef123456abcdef1234']
VALID_ID_VALUES_IDS = ['Only Nums', 'Only Letters', 'Letters and Nums']

INVALID_IDS = EMPTY_STRINGS.copy() + ['wer45poi8928749290up1234567nnpi', 'wer45poiup1234567nnpp', 'a', '123456789012345678901@']
INVALID_ID_IDS = EMPTY_STRINGS_IDS.copy() + ['id_length>22', 'id_length<22', 'One Char', 'Special Char']

VALID_URL_VALUES = ['https://song.com', 'http://hello+from+the+other+side.com']
VALID_URL_VALUES_IDS = ['https://', 'http://']

INVALID_URL_VALUES = EMPTY_STRINGS.copy() + ['htt://music.com', 'HTTPS://hello.com', 'http//', 'http:/']
INVALID_URL_VALUES_IDS = EMPTY_STRINGS_IDS.copy() + ['Invalid Protocol', 'Uppercase HTTPS', 'Missing semicolon', 'Missing Slash']

NO_DOMAIN_URL_VALUES = ['https://', 'http://']
NO_DOMAIN_URL_VALUES_IDS = ['No Domain https://', 'No Domain http://']


# #################################
# SONG AND ARTIST NAME CONSTANTS
# #################################


VALID_SONG_NAMES = ['test song', 'Test Song', 'TEST SONG', ' Test Song ']
VALID_SONG_NAMES_IDS = ['Lowercase', 'Title Case', 'Uppercase', 'Leading/Trailing Space']

VALID_ARTIST_NAMES = ['test artist', 'Test Artist', 'TEST ARTIST', ' Test Artist ']
VALID_ARTIST_NAMES_IDS = ['Lowercase', 'Title Case', 'Uppercase', 'Leading/Trailing Space']


# #################################
# MBID CONSTANTS
# #################################


VALID_MBID_VALUES = ['12345678-1234-1234-1234-123456789012', '123bc678-bcda-feda-12bc-123456bb0122']
VALID_MBID_VALUES_IDS = ['Numeric MBID', 'Alphanumeric MBID']

INVALID_MBID_VALUES = ['', ' ', '12345678-1234-1234-1234-12345678901', '12345678-1234-1234-123a4-123456789012',
                       '1234@678-1234-1234-1234-123456789012', '12345678-1234-1234-1234-1234567890g2',
                       '12345678-1234-1234-1234123456789012']
INVALID_MBID_VALUES_IDS = ['Empty String', 'Single Space', 'Too Short', 'Invalid Char', 'Special Char',
                           'Invalid End Char', 'No Hyphens']

# ################################
# NUMERIC VALIDATION CONSTANTS 
# #################################

VALID_TRACK_NUMBER_VALUES = [1, 100, 150, 199, 75]
VALID_DURATION_VALUES = [(1, 1000, .02), (7200, 7200000, 120.0), (200, 200000, 3.33)]
VALID_DURATION_VALUES_IDS = ['One Second', '2 Hours', '200 seconds']

INVALID_ENGAGEMENT_RATIO_VALUES = [-1.0, 1.001, 100.1, -100.1]
INVALID_ENGAGEMENT_RATIO_VALUES_IDS = ['Negative', 'Over 1', 'Large Positive', 'Large Negative']

INVALID_PLAYS_PER_LISTENER_VALUES = [-.00001, 2000.1, 5000.0, -100.1]
INVALID_PLAYS_PER_LISTENER_VALUES_IDS = ['Slightly Negative', 'Over Max', 'Large Over Max', 'Large Negative']

INVALID_NEGATIVE_INT_VALUES = [-1, -10000]
INVALID_NEGATIVE_INT_VALUES_IDS = ['Negative One', 'Large Negative']

VALID_SPECTRAL_CENTROID_VALUES=[0.0,5000.0,10000.0]
VALID_SPECTRAL_CENTROID_VALUES_IDS = ['Minimum','Mid_Range','Maximum']
INVALID_SPECTRAL_CENTROID_VALUES=[-.0001, -10000.0, 10000.01, 10000000.0]
INVALID_SPECTRAL_CENTROID_VALUES_IDS=['Slightly Under Min', 'Greatly Under Min', 'Slightly Over Max', 'Greatly Over Max']


VALID_CALCULATED_FIELD_VALUES = [
    (0.0, 100000, 0, 0.5, 50000),
    (0.001, 1000, 1, 1.0, 1000),
    (0.0005, 10000, 5, .25, 2500)
]
VALID_CALCULATED_FIELD_VALUES_IDS = ['Zero PPL', 'Small PPL', 'Medium PPL']

VALID_SONG_LISTENERS_VALUES = [
    (0.0, 50, 0, 0.0, 0),
    (1.0, 1, 1, 1.0, 1),
    (.5, 400, 200, .25, 100),
    (.5, 4000, 2000, .25, 1000)
]
VALID_SONG_LISTENERS_VALUES_IDS = ['Zero Values', 'Unit Values', 'Medium Values', 'Large Values']

INVALID_CALCULATED_FIELD_VALUES = [
    (0.5, 10000, 1000, 0.2, 2000),
    (0.05, 10000, 500, 0.8, 3000),
    (0.1, 10000, 750, 0.5, 2500)
]
INVALID_CALCULATED_FIELD_VALUES_IDS = ['Mismatch 1', 'Mismatch 2', 'Mismatch 3']

VALID_0_1_RANGE_VALUES=[0.0, .25, .5, .75, 1.0]
VALID_0_1_RANGE_VALUES_IDS=['Lower Boundary-0', '.25', '.5', '.75', 'Upper Boundary-1']
INVALID_0_1_RANGE_VALUES= [-.01, -10.0, np.nan, np.inf, 10.0, 1.01]
INVALID_0_1_RANGE_VALUES_IDS = ['Negative_Slight','Negative_Large', 'NaN_Value','Infinity','Too_High_Large','Too_High_Slight']


VALID_AUDIO_FEATURE_FLOATS=[(50.0, .5, .3, .385),
        (100.0, .8, .3, .61),
        (150.0, .6, .77, .679),
        (200.0, .99, 1.0, .995)]
VALID_AUDIO_FEATURE_FLOATS_IDS = ['BPM_50', 'BPM_100', 'BPM_150', 'BPM_200']

# ################################
# PARSER CONSTANTS
# #################################

AUDIO_FEATURES_REQUIRED_FIELDS = [
    'song_id', 'bpm', 'energy', 'spectral_centroid',
    'zero_crossing_rate', 'danceability', 'preview_url',
    'harmonic_ratio', 'percussive_ratio'
]
LASTFM_REQUIRED_FIELDS=['song_name', 'artist_id', 'artist_name']
LAST_FM_OPTIONAL_FIELDS=['num_song_listeners', 'mbid', 'song_url', 'on_tour', 'artist_total_listeners','artist_total_playcount','song_id','engagement_ratio','plays_per_listener']
SPOTIFY_REQUIRED_FIELDS=['song_name', 'artist_name', 'duration_ms','popularity', 'song_id', 'artist_id', 'album_id']
SPOTIFY_OPTIONAL_FIELDS=['album_title', 'album_type', 'release_date', 'release_date_precision', 'is_playable', 'album_total_tracks', 'track_number', 'is_explicit']


# ################################
# TEXT UTILS CONSTANTS
# #################################
NORMALIZE_SONG_NAME_VALUES=[
        ('Test Song', 'test song'),
        ('TEST SONG', 'test song'),
        (' TeSt SoNg ', 'test song'),
        ('test & song', 'test and song'),
        ('test song ft. usher ', 'test song'),
        ('test song feat. usher', 'test song'),
        (' ', ''),
        ("",""),
        ('@#$%', "@#$%"),
        ('A'*10, 'a'*10),
        ('song (Remix)', 'song'),
        ('song [Explicit]', 'song'),
        ('song + usher', 'song'),
        (' sOng + ARTIST (featuring usher) [REmix] short version', 'song'),
        ('café', 'café'),              
        ('Björk', 'björk'),           
        ('Björk 🎵', 'björk 🎵'),      
        ('русский текст', 'русский текст'), 
        ('日本の音楽', '日本の音楽'), 
    ]
NORMALIZE_SONG_NAME_VALUES_IDS=[f'Input:{input} Output:{output}' for input,output in NORMALIZE_SONG_NAME_VALUES]

EXTRACT_COLLABORATORS_VALUES=[
    ('', []),
    (' ', []),
    ('\t', []),
    ('song', []),
    ('song name + usher', ['usher']),
    ('song name + usher +   kesha', ['usher', 'kesha']),
    ('song name ft. usher', ['usher']),
    ('song name feat. usher', ['usher']),
    ('song name featuring usher', ['usher']),
    ('song name featuring usher (featuring kesha)', ['usher']),
    ('song name featuring u$her', ['u$her']),
    ('song_name featuring usher, kesha & ariana', ['usher', 'kesha & ariana'])]
EXTRACT_COLLABORATORS_VALUES_IDS=('Empty String', 'One Space', 'One Tab',
 'One Word (No Artist)', 'One Collaborator', 'Two Collaborators', 'One Ft.',
 'One Feat.', 'One Featuring', 'One Featuring with Parenthesis', 'Special Char in Collaborator',
 'Many Collaborators with &' )

HAS_COLLABORATORS_TEST_CASES=[
    ('Song + Artist', True),
    ('Song feat Artist', True),
    ('Song ft. Artist', True),
    ('Song featuring Artist', True),
    ('Song + Artist feat. Artist1 featuring Artist2 ft. Artist3', True),
    ('song artist', False),
    ('song and artist', False)]

SIMILARITY_SCORE_VALUES=[
        ('test', 'test', 1.0),
        ('', '', 1.0),
        ('TeST', 'test', 1.0),
        ('abc', 'xyz', 0.0),
        ('test', 'TESTING', .73),
    ]
SIMILARITY_SCORE_VALUES_IDS=[
    'Exact Match w Text', 'Exact Match Empty String', 'Exact Match Case Insensitive', 'No Match', 'Partial Match'
]