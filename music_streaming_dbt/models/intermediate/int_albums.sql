WITH flattened AS (
    SELECT DISTINCT
        album_id,
        album_title,
        artist_id,
        album_total_tracks,
        album_type
    FROM {{ ref('stg_spotify__tracks') }}
    WHERE album_id IS NOT NULL
)

SELECT * FROM flattened

