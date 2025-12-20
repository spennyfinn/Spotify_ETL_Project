from pydantic import BaseModel, field_validator, model_validator




class Spotify_Data(BaseModel):
    album_type: str 
    is_playable: bool
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



    field_validator('popularity')
    def validate_album_popularity(cls, value, info):
        if not value or value<=0:
            raise ValueError(f'{info.field_name} cannot be None or negative')
        if not isinstance(value, int):
            raise TypeError(f'{info.field_name} should be integer but is {type(value)}')
        if value >100:
            raise ValueError(f'{info.field_name} cannot be over 100')
        return int(value)
        

    @field_validator('album_total_tracks')
    def validate_album_total_tracks(cls, value, info):
        if not value or value==0:
            return 0
        if not isinstance(value, int):
            raise TypeError(f'{info.field_name} should be boolean but is {type(value)}')
        if value <1 and value > 100:
            raise ValueError(f'{info.field_name} should be positive and less than 100')
        return int(value)


    @field_validator('artist_id', 'song_name', 'artist_name', 'album_id' , 'artist_id')
    def validate_required_strings(cls, value, info):
        if not value or value =='':
            raise ValueError(f"{info.field_name} can't be None or and empty string : {value}")
        if not isinstance(value, str):
            raise TypeError(f'{info.field_name} should be boolean but is {type(value)}')
        if len(value.strip())==0:
            raise ValueError(f"{info.field_name} can't be an empty string")
        return value.strip().lower() if value in ['song_name', 'artist_name'] else value.strip()


    @field_validator('album_type', 'song_id', 'release_date_precision', 'release_date')
    def validate_optional_strings(cls, value, info):
        if not value or value=='':
            return None
        if not isinstance(value, str):
            raise TypeError(f'{info.field_name} should be boolean but is {type(value)}')
        return value.strip()
            

    @field_validator('on_tour', 'is_playable')
    def validate_on_tour(cls, value, info):
        if not value:
            return False
        if not isinstance(value, bool):
            raise TypeError(f'{info.field_name} should be boolean but is {type(value)}')
        return bool(value)

    
    @field_validator('track_number')
    def validate_track_number(cls, value, info):
        if not value:
            return 0
        if not isinstance(value, int):
            raise TypeError(f"{info.field_name} should be an integer but it is a {type(value)}")
        if value<0 and value>50:
            raise ValueError(f"{info.field_name} should be between 0-50 but was: {value}")
        return int(value)
    
    
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




