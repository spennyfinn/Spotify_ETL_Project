
WITH final AS (
    SELECT 
        song_id,
        bpm,
        energy,
        spectral_centroid,
        zero_crossing_rate,
        harmonic_ratio,
        percussive_ratio,
        danceability,
        preview_url
    FROM {{ ref('stg_audio__features') }}
)

SELECT * FROM final