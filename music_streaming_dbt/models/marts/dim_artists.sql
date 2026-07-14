WITH track_artists AS (
    SELECT
        artist_id,
        MAX(artist_name) AS artist_name
    FROM {{ ref('stg_spotify__tracks') }}
    WHERE artist_id IS NOT NULL
    GROUP BY artist_id
),

api_artists AS (
    SELECT
        artist_id,
        artist_name,
        artist_popularity,
        artist_followers
    FROM {{ ref('stg_spotify__artists') }}
),

lastfm_artists AS (
    SELECT
        artist_id,
        MAX(on_tour) AS on_tour,
        MAX(artist_total_listeners) AS artist_total_listeners,
        MAX(artist_total_playcount) AS artist_total_playcount,
        MAX(plays_per_listener) AS plays_per_listener
    FROM {{ ref('stg_lastfm') }}
    WHERE artist_id IS NOT NULL
    GROUP BY artist_id
),

all_artist_ids AS (
    SELECT artist_id FROM track_artists
    UNION
    SELECT artist_id FROM api_artists
)

SELECT
    ids.artist_id,
    COALESCE(api.artist_name, track.artist_name) AS artist_name,
    api.artist_popularity,
    api.artist_followers,
    lastfm.on_tour,
    lastfm.artist_total_listeners,
    lastfm.artist_total_playcount,
    lastfm.plays_per_listener
FROM all_artist_ids AS ids
LEFT JOIN track_artists AS track USING (artist_id)
LEFT JOIN api_artists AS api USING (artist_id)
LEFT JOIN lastfm_artists AS lastfm USING (artist_id)
