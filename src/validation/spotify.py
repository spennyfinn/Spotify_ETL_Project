
from pydantic import BaseModel, field_validator, model_validator
import string
from typing import Any



class Spotify_Data(BaseModel):
    album_type: Any 
    is_playable: Any
    album_id: Any
    song_name: Any
    artist_name: Any
    release_date: Any
    release_date_precision: Any
    album_total_tracks: Any
    track_number: Any
    is_explicit: Any
    popularity: Any
    song_id: Any
    duration_ms: Any
    duration_seconds: Any
    duration_minutes: Any
    artist_id: Any
    album_title:Any


    @field_validator('album_title')
    def validate_album_title(cls, value, info):
        if value =='':
            raise ValueError(f'{info.field_name} cannot be an empty string')
        if type(value) is not str:
            raise TypeError(f'{info.field_name} must be a string but was {type(value)}')
        if len(value.strip())==0:
            raise ValueError(f'{info.field_name} cannot only be whitespace')
        return value.strip().lower()



    @field_validator('duration_ms')
    def valdiate_duration_ms(cls, value, info):
        if type(value) is not int:
            raise TypeError(f'{info.field_name} must be an integer but was {type(value)}')        
        if value < 1000 or value > 7200000:
            raise ValueError(f'{info.field_name} should be longer than one second and less than 2 hours')
        return int(value)


    @field_validator('artist_id', 'song_id', 'album_id')
    def validate_spotify_ids(cls, value, info):
        if type(value) is not str:
            raise TypeError(f'{info.field_name} must be a string but got {type(value)}')
        stripped= value.strip()
        if value =='' or len(stripped)==0:
            raise ValueError(f"{info.field_name} cannot be an empty string or whitespace")
        if len(value)!=22:
            raise ValueError(f'{info.field_name} must be 22 characters, but got {len(value)}')
        base62 = string.ascii_letters + string.digits
        if not all(c in base62 for c in value):
            raise ValueError(f"{info.field_name} has invalid characters: {value}")
        return stripped

    @field_validator('album_type')
    def validate_album_type(cls, value, info):
        if type(value) is not str:
            raise TypeError(f"{info.field_name} should be a string but it was {type(value)}")
        valid_types = ['single', 'album', 'compilation']
        if value not in valid_types:
            raise ValueError(f'{info.field_name} must be of {valid_types} but was {value}')
        return value.strip().lower()


    @field_validator('release_date_precision')
    def validate_release_date_precision(cls, value, info):
        if type(value) is not str:
            raise TypeError(f"{info.field_name} should be a string but it was {type(value)}")
        if value not in ['day', 'month', 'year']:
            raise ValueError(f'{info.field_name} should be either "day", "month", or "year" but the value was {value}')
        return str(value.strip().lower())


    @field_validator('popularity')
    def validate_album_popularity(cls, value, info):
        if value is None or type(value) is not int:
            raise TypeError(f'{info.field_name} should be an integer but is {type(value)}')
        if value <0 or value >100:
            raise ValueError(f'{info.field_name} cannot be over 100')
        return int(value)
        

    @field_validator('album_total_tracks')
    def validate_album_total_tracks(cls, value, info):
        if value is None:
            return 0
        if type(value) is not int:
            raise TypeError(f'{info.field_name} should be an integer but is {type(value)}')
        if value < 0 or value > 100:
            raise ValueError(f'{info.field_name} should be positive and less than 100')
        return int(value)


    @field_validator('artist_id', 'song_name', 'artist_name', 'album_id')
    def validate_required_strings(cls, value, info):
        if type(value) is not str:
            raise TypeError(f'{info.field_name} should be string but is {type(value)}')
        if len(value.strip())==0:
            raise ValueError(f"{info.field_name} can't be an empty string")
        return value.strip().lower() if value in ['song_name', 'artist_name'] else value.strip()
            

    @field_validator('is_explicit', 'is_playable')
    def validate_bools(cls, value, info):
        if type(value) is not bool:
            raise TypeError(f'{info.field_name} should be boolean but is {type(value)}')
        return bool(value)

    
    @field_validator('track_number')
    def validate_track_number(cls, value, info):
        if type(value) is not int:
            raise TypeError(f'{info.field_name} should be an integer but got {type(value)}')
        if value < 0 or value > 100:
            raise ValueError(f"{info.field_name} should be between 0-50 but was: {value}")
        return int(value)
    
    @field_validator('duration_seconds')
    def validate_duration_seconds(cls, value, info):
        if type(value) is not int:
            raise TypeError(f'{info.field_name} should be an integer but got {type(value)}')
        if value < 1 or value > 7200:
            raise ValueError(f'{info.field_name} should be longer than one second and shorter than 2 hours')
        return int(value)

    @field_validator('duration_minutes')
    def validate_duration_minutes(cls, value, info):
        if type(value) is not float:
            raise TypeError(f'{info.field_name} should be a float but got {type(value)}')
        if value < .0166 or value > 120.0:
            raise ValueError(f'{info.field_name} should be longer than one second and shorter than 2 hours')
        return float(value)

            

    @model_validator(mode='after')
    def check_time(cls, model):
        if model.duration_ms is not None and model.duration_seconds is not None:
            duration_seconds= model.duration_ms//1000
            if duration_seconds!= model.duration_seconds:
                raise ValueError(f'duration_seconds was calculated incorrectly: calcualted_value {duration_seconds} transformed_value: {model.duration_seconds}')
        if model.duration_seconds is not None and model.duration_minutes is not None:
            duration_minutes=round(model.duration_seconds/60,2)
            if duration_minutes != model.duration_minutes:
                raise ValueError(f'duration_minutes was calculated incorrectly: calcualted_value {duration_minutes} transformed_value: {model.duration_minutes}')
        return model




