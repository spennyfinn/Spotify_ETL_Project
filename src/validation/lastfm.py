from typing import Any
from llvmlite.ir.values import Value
from pydantic import  BaseModel, field_validator, model_validator
import re
import string



class LastFm(BaseModel):
    song_name: Any
    artist_name: Any
    artist_name: Any
    num_song_listeners: Any
    mbid:Any
    on_tour: Any
    song_id: Any
    artist_total_playcount: Any
    artist_total_listeners: Any
    plays_per_listener: Any
    engagement_ratio:Any
    artist_id: Any


    @field_validator('num_song_listeners', 'artist_total_playcount', 'artist_total_listeners')
    def validate_num_song_listeners_or_artist_stats(cls, value, info):
        if type(value) is not int:
            raise TypeError(f'{info.field_name} needs to be a whole number, but got {type(value).__name__}')
        if value < 0:
            raise ValueError(f"{info.field_name} can't be negative (got {value}) - that doesn't make sense!")
        return int(value)

    @field_validator('plays_per_listener')
    def validate_plays_per_listener(cls, value, info):
        if value is None:
            return None
        if type(value) is not float:
            raise TypeError(f'{info.field_name} should be a decimal number, but got {type(value).__name__}')
        if value < 0.0 or value > 10000:
            raise ValueError(f"{info.field_name} should be between 0 and 2000, but got {value}")
        return float(value)

    

    @field_validator('engagement_ratio')
    def validate_engagement_ratio(cls, value, info):
        if type(value) is not float:
            raise TypeError(f'{info.field_name} needs to be a decimal number between 0 and 1, but got {type(value).__name__}')
        if value < 0.0:
            raise ValueError(f"{info.field_name} must be greater than 0 but got: {Value}")
        return float(value)
        
    @field_validator('on_tour')
    def validate_on_tour(cls, value, info):
        '''Make sure the on_tour field is a simple yes/no value'''
        if type(value) is not bool:
            raise TypeError(f"{info.field_name} should be True or False, but got {value}")
        return bool(value)
    
    @field_validator('song_name', 'artist_name')
    def validate_names(cls, value, info):
        if type(value) is not str:
            raise TypeError(f"{info.field_name} needs to be text, but got {type(value).__name__}")
        if len(value.strip()) == 0:
            raise ValueError(f"{info.field_name} can't be blank or empty")
        return value.strip().lower()

    @field_validator('song_id', 'artist_id')
    def validate_ids(cls, value, info):
        '''Check that ID fields contain valid characters'''
        if type(value) is not str:
            raise TypeError(f"{info.field_name} should be a text string, but got {type(value).__name__}")
        stripped = value.strip()
        if len(stripped)!=22:
            raise ValueError(f'{info.field_name} must be 22 characters, but got {len(value)}')
        base62 = string.digits + string.ascii_letters
        if not all(c in base62 for c in stripped):
            raise ValueError(f"{info.field_name} contains invalid characters - only letters and numbers allowed")
        return stripped
    
    
    @field_validator('mbid')
    def validate_mbid(cls, value, info):
        '''Make sure MBID follows the standard MusicBrainz format'''
        if value is None:
            return None
        if type(value) is not str:
            raise TypeError(f"{info.field_name} needs to be a text string, but got {type(value).__name__}")
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        if not re.match(pattern, value.lower().strip()):
            raise ValueError(f'{info.field_name} must be a valid MusicBrainz ID format (like: 12345678-abcd-1234-5678-123456789012)')
        return value.strip().lower()
    

    @model_validator(mode='after')
    def check_calculations(cls, model):
        "Make sure calculated fields match their expected values"
        errors = []
        if model.artist_total_listeners is not None and model.artist_total_playcount is not None and model.plays_per_listener is not None:
            calculated_ppl = round(model.artist_total_playcount / model.artist_total_listeners, 5)
            if calculated_ppl != model.plays_per_listener:
                errors.append(f"plays_per_listener doesn't match the calculation: expected {calculated_ppl}, but got {model.plays_per_listener}")

        if model.engagement_ratio is not None and model.artist_total_listeners is not None and model.num_song_listeners is not None:
            calculated_er = round(model.num_song_listeners / model.artist_total_listeners, 5)
            if calculated_er != model.engagement_ratio:
                errors.append(f"engagement_ratio doesn't match the calculation: expected {calculated_er}, but got {model.engagement_ratio}")

        if errors:
            raise ValueError("; ".join(errors))

        return model

