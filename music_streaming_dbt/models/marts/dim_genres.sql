
WITH distinct_genres AS(
SELECT DISTINCT
    genre_name
FROM {{ ref('int_artist__genres') }}
)

SELECT 
    ROW_NUMBER() OVER(ORDER BY genre_name) AS genre_id,
    genre_name
FROM distinct_genres