WITH source AS (
    SELECT
        artist_id,
        _run_id,
        _loaded_at,
        parse_json(payload::varchar) AS payload
    FROM {{ source('raw', 'raw_spotify_artists') }}
),

flattened AS(
SELECT 
    trim(artist_id) AS artist_id,
    lower(trim(payload:artist_name::varchar)) AS artist_name,
    payload:follower_count::int AS artist_followers,
    payload:popularity::int AS artist_popularity,
    payload:genres AS genres,
    coalesce(array_size(payload:genres), 0) > 0 AS has_genres,
    payload:source::varchar AS source,
    _run_id,
    _loaded_at
FROM source
WHERE artist_id IS NOT NULL
    AND payload:artist_name IS NOT NULL
    AND payload:follower_count::int > 0
    AND payload:popularity::int BETWEEN 0 AND 100
    AND payload:source IS NOT NULL
    AND _loaded_at IS NOT NULL
QUALIFY ROW_NUMBER() OVER(
    PARTITION BY artist_id
    ORDER BY _loaded_at DESC 
) = 1
)

SELECT * FROM flattened