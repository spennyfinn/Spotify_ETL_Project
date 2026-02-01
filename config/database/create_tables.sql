CREATE TABLE artists (
    artist_id TEXT PRIMARY KEY,  --SP     
    artist_name TEXT NOT NULL CHECK(length(artist_name)>0),    --SP                     
    on_tour BOOLEAN DEFAULT FALSE, --LFM
    total_listeners BIGINT DEFAULT 0 CHECK(total_listeners >= 0),    --LFM
    total_playcount BIGINT DEFAULT 0 CHECK(total_playcount>=0),   --LFM 
    plays_per_listener FLOAT,   --LFM
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    artist_popularity INT,
    artist_followers INT,
    has_genres BOOLEAN
);

CREATE TABLE albums(
    album_id TEXT PRIMARY KEY, --SP
    album_title TEXT NOT NULL,  --SP
    artist_id TEXT REFERENCES artists(artist_id), --SP
    album_type TEXT CHECK(album_type IN ('single', 'compilation', 'album')),  --SP
    album_total_tracks INT CHECK(album_total_tracks>0 AND album_total_tracks<=200), --SP
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
);

CREATE TABLE songs(
    song_id TEXT PRIMARY KEY, --SP
    song_name TEXT NOT NULL, --SP
    artist_id TEXT REFERENCES artists(artist_id),
    album_id TEXT REFERENCES albums(album_id),
    song_listeners INT DEFAULT 0 CHECK(song_listeners >=0), --SP
    mbid TEXT, -- LFM
    duration_ms INT CHECK(duration_ms > 1000 AND duration_ms < 10800000), --SP
    duration_seconds INT CHECK (duration_seconds >1 AND duration_seconds < 10800), --SP
    duration_minutes FLOAT CHECK (duration_minutes > .016 AND duration_minutes < 180.0), --SP
    engagement_ratio FLOAT CHECK (engagement_ratio >=0),  --LFM
    release_date TEXT, --SP
    release_date_precision TEXT CHECK (release_date_precision IN ('year', 'day', 'month')), --SP
    is_explicit BOOLEAN, --SP
    popularity INT CHECK (popularity >=0 AND popularity <= 100), --SP
    track_number INT CHECK (track_number >0 AND track_number<=100), --SP
    is_playable BOOLEAN, --SP
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE song_audio_features(
    song_id TEXT PRIMARY KEY REFERENCES songs(song_id) ON DELETE CASCADE,
    bpm FLOAT CHECK(bpm >= 30 AND bpm <=300),
    energy FLOAT CHECK(energy >= 0 AND energy <= 1),
    spectral_centroid FLOAT CHECK (spectral_centroid >= 0 AND spectral_centroid <=10000),
    zero_crossing_rate FLOAT CHECK(zero_crossing_rate >= 0 AND zero_crossing_rate <= 1),
    danceability FLOAT CHECK(danceability >= 0 AND danceability <= 1),
    preview_url TEXT,
    harmonic_ratio FLOAT CHECK(harmonic_ratio >= 0 AND harmonic_ratio <= 1),
    percussive_ratio FLOAT CHECK(percussive_ratio >= 0 AND percussive_ratio <= 1),
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE genres(
    genre_id SERIAL PRIMARY KEY,
    genre_name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE artist_genres(
    artist_id TEXT REFERENCES artists(artist_id) ON DELETE CASCADE,
    genre_id INT REFERENCES genres(genre_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (artist_id, genre_id)
);



--INDEXES
CREATE INDEX idx_songs_engagement_ratio ON songs(engagement_ratio);
CREATE INDEX idx_songs_release_date ON songs(release_date);
CREATE INDEX idx_albums_total_tracks ON albums(album_total_tracks);
CREATE INDEX idx_artist_name ON artists(artist_name);
CREATE INDEX idx_songs_popularity ON songs(popularity DESC);
