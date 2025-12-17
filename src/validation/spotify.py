from pydantic import BaseModel, field_validator, model_validator




class Spotify_Data(BaseModel):
    album_type: str
    is_playable:bool
    album_id: str
    song_name: str
    artist_name: str
    release_date: str
    release_date_precision: str
    album_total_tracks: int
    track_number: int
    is_explicit: bool
    popularity: int
    song_id: str
    duration_ms: int
    duration_seconds: int
    duration_minutes: float
    artist_id: str
    album_title:str


    @field_validator("song_name", "artist_name", "album_id", "album_type", "release_date_precision", mode="before")
    def normalize_strings(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @model_validator(mode='after')
    def check_time(cls, model):

        if model.duration_ms is not None and model.duration_seconds is not None:
            duration_seconds= model.duration_ms//1000
            if duration_seconds!= model.duration_seconds:
                raise ValueError(f'duration_seconds was calcualted incorrectly: calcualted_value {duration_seconds} transformed_value: {model.duration_seconds}')
        if model.duration_seconds is not None and model.duration_minutes is not None:
            duration_minutes=round(model.duration_seconds/60,2)
            if duration_minutes != model.duration_minutes:
                raise ValueError(f'duration_minutes was calcualted incorrectly: calcualted_value {duration_minutes} transformed_value: {model.duration_minutes}')
        return model




