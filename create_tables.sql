CREATE TABLE artists (
    artist_id TEXT PRIMARY KEY,  --LFM or generated       
    artist_name TEXT UNIQUE NOT NULL,    --LFM       
    artist_url TEXT,   --LFM                 
    on_tour BOOLEAN DEFAULT FALSE, --LFM
    total_listeners BIGINT DEFAULT 0,    --LFM
    total_playcount BIGINT DEFAULT 0 ,   --LFM 
    plays_per_listener FLOAT DEFAULT 0   --LFM
);

CREATE TABLE albums(
    album_id TEXT PRIMARY KEY, --SP
    album_title TEXT NOT NULL,  --LFM
    artist_name TEXT REFERENCES artists(artist_name), --LFM
    album_type TEXT,  --SP
    album_total_tracks INT, --SP
    UNIQUE(album_title, artist_name)
);

CREATE TABLE similar_artists( --ALL LFM
    artist_name TEXT REFERENCES artists(artist_name),
    similar_artist_name TEXT,
    PRIMARY KEY (artist_name, similar_artist_name)
);

CREATE TABLE songs(
    song_name TEXT, --LFM
    artist_id TEXT REFERENCES artists(artist_id),
    album_id TEXT REFERENCES albums(album_id),
    rank INT UNIQUE, --LFM
    song_listeners INT, --LFM
    duration_seconds INT, --LFM
    duration_minutes FLOAT, --LFM
    duration_ms INT, --SP
    song_id TEXT, --LFM
    song_url TEXT, --LFM
    engagement_ratio FLOAT,  --LFM
    release_date TEXT, --SP
    release_date_precision TEXT, --SP
    is_explicit BOOLEAN, --SP
    popularity INT, --SP
    track_number INT, --SP
    PRIMARY KEY (song_name, artist_id)
);

CREATE TABLE tags( --ALL LFM
    song_name TEXT,
    artist_id TEXT,
    tag TEXT,
    PRIMARY KEY (song_name, artist_id, tag),
    FOREIGN KEY (song_name, artist_id)
        REFERENCES songs(song_name, artist_id)
);


 