
SELECT 
    ag.artist_id,
    g.genre_id
FROM {{ref('int_artist__genres')}} as ag
INNER JOIN {{ref('dim_genres')}} as g
    ON ag.genre_name = g.genre_name

