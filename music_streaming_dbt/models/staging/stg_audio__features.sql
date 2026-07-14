WITH source AS (
    SELECT
        song_id,
        _run_id,
        _loaded_at,
        parse_json(payload::varchar) AS payload
    FROM {{ source('raw', 'raw_audio_features') }}
),


flattened AS(
    SELECT 
        trim(song_id::varchar) AS song_id,
        round(payload:bpm::float, 3) AS bpm,
        round(payload:energy::float, 5) AS energy,
        round(payload:spectral_centroid::float, 3) AS spectral_centroid,
        round(payload:zero_crossing_rate::float, 5) AS zero_crossing_rate,
        trim(payload:preview_url::varchar) AS preview_url,
        least(round (payload:harmonic_ratio::float, 5), 1.0) AS harmonic_ratio,
        least(round( payload:percussive_ratio::float, 5), 1.0) AS percussive_ratio,
        round(
            (least ( payload:bpm::float / 200, 1.0 ) * 0.3) 
            + (payload:energy::float * 0.5) 
            + (payload:zero_crossing_rate::float * 0.2),
             5)  
            AS danceability,
        trim(payload:source::varchar) AS source,
        _run_id,
        _loaded_at
    FROM source
    WHERE 
            song_id IS NOT NULL
        AND payload:harmonic_ratio::float BETWEEN 0 AND 1
        AND payload:percussive_ratio::float BETWEEN 0 AND 1
        AND payload:source iS NOT NULL
        AND payload:preview_url IS NOT NULL
        AND payload:bpm::float BETWEEN 30 and 300
        AND payload:energy::float BETWEEN 0 AND 1
        AND payload:zero_crossing_rate::float BETWEEN 0 AND 1
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY song_id
        ORDER BY _loaded_at DESC
    ) =1
)


SELECT * FROM flattened