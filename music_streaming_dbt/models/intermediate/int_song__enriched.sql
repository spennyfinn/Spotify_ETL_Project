
WITH flattened AS (
    SELECT
        spotify.song_id,
        spotify.song_name,
        spotify.popularity,
        spotify.artist_id,
        spotify.album_id,
        spotify.duration_ms, 
        spotify.duration_seconds,
        spotify.duration_minutes,
        spotify.track_number,
        spotify.release_date,
        spotify.release_date_precision,
        spotify.is_playable,
        spotify.is_explicit,
        lastfm.num_song_listeners,
        lastfm.engagement_ratio,
        lastfm.mbid
    FROM {{ref('stg_spotify__tracks') }} AS spotify
    LEFT JOIN {{ref('stg_lastfm')}} AS lastfm
    ON spotify.song_id = lastfm.song_id
    WHERE 
        spotify.song_id IS NOT NULL
)

SELECT * FROM flattened