"""Test data for text_processing_utils unit tests."""

WRONG_STRING_TYPE = [False, 0, 1.9, [], {}, None]
WRONG_STRING_TYPE_IDS = ["Boolean", "Integer", "Float", "Empty List", "Empty Dict", "None"]

WRONG_STRING_PAIRS = [(value, value) for value in WRONG_STRING_TYPE]
WRONG_STRING_PAIRS_IDS = [f"{value} Pair" for value in WRONG_STRING_TYPE]

NORMALIZE_SONG_NAME_VALUES = [
    ("Test Song", "test song"),
    ("TEST SONG", "test song"),
    (" TeSt SoNg ", "test song"),
    ("test & song", "test and song"),
    ("test song ft. usher ", "test song"),
    ("test song feat. usher", "test song"),
    (" ", ""),
    ("", ""),
    ("@#$%", "@#$%"),
    ("A" * 10, "a" * 10),
    ("song (Remix)", "song"),
    ("song [Explicit]", "song"),
    ("song + usher", "song"),
    (" sOng + ARTIST (featuring usher) [REmix] short version", "song"),
    ("café", "café"),
    ("Björk", "björk"),
    ("Björk 🎵", "björk 🎵"),
    ("русский текст", "русский текст"),
    ("日本の音楽", "日本の音楽"),
]
NORMALIZE_SONG_NAME_VALUES_IDS = [
    f"Input:{input} Output:{output}" for input, output in NORMALIZE_SONG_NAME_VALUES
]

EXTRACT_COLLABORATORS_VALUES = [
    ("", []),
    (" ", []),
    ("\t", []),
    ("song", []),
    ("song name + usher", ["usher"]),
    ("song name + usher +   kesha", ["usher", "kesha"]),
    ("song name ft. usher", ["usher"]),
    ("song name feat. usher", ["usher"]),
    ("song name featuring usher", ["usher"]),
    ("song name featuring usher (featuring kesha)", ["usher"]),
    ("song name featuring u$her", ["u$her"]),
    ("song name featuring usher, kesha & ariana", ["usher", "kesha & ariana"]),
]
EXTRACT_COLLABORATORS_VALUES_IDS = (
    "Empty String",
    "One Space",
    "One Tab",
    "One Word (No Artist)",
    "One Collaborator",
    "Two Collaborators",
    "One Ft.",
    "One Feat.",
    "One Featuring",
    "One Featuring with Parenthesis",
    "Special Char in Collaborator",
    "Many Collaborators with &",
)

HAS_COLLABORATORS_TEST_CASES = [
    ("Song + Artist", True),
    ("Song feat Artist", True),
    ("Song ft. Artist", True),
    ("Song featuring Artist", True),
    ("Song + Artist feat. Artist1 featuring Artist2 ft. Artist3", True),
    ("song artist", False),
    ("song and artist", False),
]

SIMILARITY_SCORE_VALUES = [
    ("test", "test", 1.0),
    ("", "", 1.0),
    ("TeST", "test", 1.0),
    ("abc", "xyz", 0.0),
    ("test", "TESTING", 0.73),
]
SIMILARITY_SCORE_VALUES_IDS = [
    "Exact Match w Text",
    "Exact Match Empty String",
    "Exact Match Case Insensitive",
    "No Match",
    "Partial Match",
]


VALID_RAW_LASTFM = {
    "song_id": "abc123",
    "original_song_name": "blinding lights",
    "original_artist_name": "the weeknd",
    "artist_id": "artist1",
    "listeners": 1000,
    "artist_listeners": 1_000_000,
    "artist_playcount": 30_000_000,
    "source": "Lastfm",
}

VALID_RAW_AUDIO_FEATURES = {
    "song_id": "track_xyz",
    "bpm": 120.5,
    "energy": 0.65,
    "zero_crossing_rate": 0.08,
    "harmonic_ratio": 0.7,
    "percussive_ratio": 0.3,
    "preview_url": "https://p.scdn.co/mp3-preview/example",
    "source": "Librosa",
}

VALID_RAW_SPOTIFY_TRACKS = {
    "song_id": "4uLU6hMCjMI75M1A2tKUQC",
    "name": "Blinding Lights",
    "artist_id": "1Xyo4u8uXC1ZmMpatF05PJ",
    "duration_ms": 200_040,
    "source": "Spotify",
}

VALID_RAW_SPOTIFY_ARTISTS = {
    "artist_id": "1Xyo4u8uXC1ZmMpatF05PJ",
    "artist_name": "The Weeknd",
    "follower_count": 50_000_000,
    "popularity": 95,
    "source": "Spotify",
}

RAW_LOAD_TABLE_CASES = [
    ("raw_lastfm", "song_id", VALID_RAW_LASTFM),
    ("raw_audio_features", "song_id", VALID_RAW_AUDIO_FEATURES),
    ("raw_spotify_tracks", "song_id", VALID_RAW_SPOTIFY_TRACKS),
    ("raw_spotify_artists", "artist_id", VALID_RAW_SPOTIFY_ARTISTS),
]
RAW_LOAD_TABLE_CASE_IDS = [
    "lastfm",
    "audio_features",
    "spotify_tracks",
    "spotify_artists",
]

RAW_PAYLOAD_SHAPE_CASES = [
    ("raw_lastfm", "song_id", VALID_RAW_LASTFM, "song_id", ("source", "Lastfm")),
    (
        "raw_audio_features",
        "song_id",
        VALID_RAW_AUDIO_FEATURES,
        "song_id",
        ("source", "Librosa"),
    ),
    (
        "raw_spotify_tracks",
        "song_id",
        VALID_RAW_SPOTIFY_TRACKS,
        "song_id",
        ("name", "Blinding Lights"),
    ),
    (
        "raw_spotify_artists",
        "artist_id",
        VALID_RAW_SPOTIFY_ARTISTS,
        "artist_id",
        ("popularity", 95),
    ),
]
RAW_PAYLOAD_SHAPE_CASE_IDS = RAW_LOAD_TABLE_CASE_IDS