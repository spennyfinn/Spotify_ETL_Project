from src.load.snowflake_loader import load_raw_records


success, errors = load_raw_records(
    table ='raw_spotify_tracks',
    records=[{
        "song_id": "test112",
        "name": "song",
        "artist_id": "artist1",
        "duration_ms": 10000,
        "source": "Spotify",
    }],
    id_columns= "song_id",
    run_id = "run1" )



print(success, errors)