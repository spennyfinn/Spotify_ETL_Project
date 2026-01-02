
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
        if value == '':
            raise ValueError(f'{info.field_name} can\'t be completely empty')
        if type(value) is not str:
            raise TypeError(f'{info.field_name} should be text, but got {type(value).__name__}')
        if len(value.strip()) == 0:
            raise ValueError(f'{info.field_name} can\'t be just spaces')
        return value.strip().lower()



    @field_validator('duration_ms')
    def validate_duration_ms(cls, value, info):
        if type(value) is not int:
            raise TypeError(f'{info.field_name} needs to be a whole number (milliseconds), but got {type(value).__name__}')
        if value < 1000 or value > 10800000:
            raise ValueError(f'{info.field_name} should be between 1 second and 3 hours long')
        return int(value)


    @field_validator('artist_id', 'song_id', 'album_id')
    def validate_spotify_ids(cls, value, info):
        if type(value) is not str:
            raise TypeError(f'{info.field_name} should be a text string, but got {type(value).__name__}')
        stripped = value.strip()
        if value == '' or len(stripped) == 0:
            raise ValueError(f"{info.field_name} is required and can't be empty")
        if len(value) != 22:
            raise ValueError(f'Spotify {info.field_name}s must be exactly 22 characters (got {len(value)})')
        base62 = string.ascii_letters + string.digits
        if not all(c in base62 for c in value):
            raise ValueError(f"{info.field_name} contains characters that aren't allowed in Spotify IDs")
        return stripped

    @field_validator('album_type')
    def validate_album_type(cls, value, info):
        if type(value) is not str:
            raise TypeError(f"{info.field_name} should be text, but got {type(value).__name__}")
        valid_types = ['single', 'album', 'compilation']
        if value not in valid_types:
            raise ValueError(f'{info.field_name} must be one of: {", ".join(valid_types)} (got "{value}")')
        return value.strip().lower()


    @field_validator('release_date_precision')
    def validate_release_date_precision(cls, value, info):
        if type(value) is not str:
            raise TypeError(f"{info.field_name} should be text, but got {type(value).__name__}")
        if value not in ['day', 'month', 'year']:
            raise ValueError(f'{info.field_name} must be "day", "month", or "year" (got "{value}")')
        return str(value.strip().lower())


    @field_validator('popularity')
    def validate_popularity(cls, value, info):
        if value is None or type(value) is not int:
            raise TypeError(f'{info.field_name} should be a whole number, but got {type(value).__name__}')
        if value < 0 or value > 100:
            raise ValueError(f'{info.field_name} represents a percentage, so it must be between 0 and 100 (got {value})')
        return int(value)
        

    @field_validator('album_total_tracks')
    def validate_album_total_tracks(cls, value, info):
        if value is None:
            return 0
        if type(value) is not int:
            raise TypeError(f'{info.field_name} should be a whole number, but got {type(value).__name__}')
        if value < 0 or value > 1000:
            raise ValueError(f'{info.field_name} should be between 0 and 1000 tracks')
        return int(value)


    @field_validator('song_name', 'artist_name')
    def validate_required_strings(cls, value, info):
        if type(value) is not str:
            raise TypeError(f'{info.field_name} should be text, but got {type(value).__name__}')
        if len(value.strip()) == 0:
            raise ValueError(f"{info.field_name} is required and can't be empty")
        return value.strip().lower()
            

    @field_validator('is_explicit', 'is_playable')
    def validate_bools(cls, value, info):
        if type(value) is not bool:
            raise TypeError(f'{info.field_name} should be True or False, but got {value}')
        return bool(value)

    
    @field_validator('track_number')
    def validate_track_number(cls, value, info):
        if type(value) is not int:
            raise TypeError(f'{info.field_name} should be a whole number, but got {type(value).__name__}')
        if value < 0 or value > 1000:
            raise ValueError(f"{info.field_name} should be between 1 and 1000 (got {value})")
        return int(value)
    
    @field_validator('duration_seconds')
    def validate_duration_seconds(cls, value, info):
        if type(value) is not int:
            raise TypeError(f'{info.field_name} should be a whole number, but got {type(value).__name__}')
        if value < 1 or value > 10800:
            raise ValueError(f'{info.field_name} should be between 1 second and 3 hours (10800 seconds)')
        return int(value)

    @field_validator('duration_minutes')
    def validate_duration_minutes(cls, value, info):
        if type(value) is not float:
            raise TypeError(f'{info.field_name} should be a decimal number, but got {type(value).__name__}')
        if value < 0.0166 or value > 180.0:
            raise ValueError(f'{info.field_name} should be between about 1 second (0.02 minutes) and 3 hours (180 minutes)')
        return float(value)

            

    @model_validator(mode='after')
    def check_time(cls, model):
        if model.duration_ms is not None and model.duration_seconds is not None:
            duration_seconds = model.duration_ms // 1000
            if duration_seconds != model.duration_seconds:
                raise ValueError(f'duration_seconds doesn\'t match the calculation from duration_ms: expected {duration_seconds} seconds, but got {model.duration_seconds}')
        if model.duration_seconds is not None and model.duration_minutes is not None:
            duration_minutes = round(model.duration_seconds / 60, 2)
            if duration_minutes != model.duration_minutes:
                raise ValueError(f'duration_minutes doesn\'t match the calculation from duration_seconds: expected {duration_minutes} minutes, but got {model.duration_minutes}')
        return model




