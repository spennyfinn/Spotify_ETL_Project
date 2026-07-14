WITH flattened AS (
    SELECT
        artist_id,
        lower(trim(f.value::varchar)) AS genre_name
    FROM {{ ref('stg_spotify__artists') }},
    LATERAL FLATTEN(input => genres) AS f
    WHERE f.value IS NOT NULL
        AND has_genres = true
)

SELECT DISTINCT artist_id, genre_name FROM flattened
