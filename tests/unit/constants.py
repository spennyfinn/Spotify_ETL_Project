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
