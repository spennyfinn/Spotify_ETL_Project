WITH final AS(
SELECT 
    song_id,
    artist_id,
    album_id,
    popularity,
    engagement_ratio,
    num_song_listeners
FROM {{ref('int_song__enriched')}}
)

SELECT * FROM final