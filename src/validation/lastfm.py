from typing import Any, Optional
from numba import bool_
from pydantic import  BaseModel, field_validator, model_validator
import re
import string



class LastFm(BaseModel):
    song_name: Any
    artist_name: Any
    artist_name: Any
    num_song_listeners: Any
    song_url: Any
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
            raise TypeError(f'{info.field_name} is supposed to be an integer but is: {type(value)}')
        if value<0:
            raise ValueError(f"{info.field_name} has a negative value when it shouldn't: {value}")
        return int(value)

    @field_validator('plays_per_listener')
    def validate_plays_per_listener(cls, value, info):
        if value is None:
            return None
        if type(value) is not float:
            raise TypeError(f'{info.field_name} is supposed to be a float but is: {type(value)}')
        if value<0.0 or value >2000:
            raise ValueError(f"{info.field_name} should be between 0 and 2000 but it was: {value}")
        return float(value)

    

    @field_validator('engagement_ratio')
    def validate_engagement_ratio(cls, value, info):
        if type(value) is not float:
            raise TypeError(f'{info.field_name} is supposed to be a float value but is: {type(value)}')
        if value<0.0 or value>1.0:
            raise ValueError(f"{info.field_name} should be between 0 and 1 but it was: {value}")
        return float(value)
        
    # Ensures that boolean columns only have values of 0/1
    @field_validator('on_tour')
    def validate_on_tour(cls, value, info):
        '''Ensure the on_tour values are boolean'''
        if type(value) is not bool:
            raise TypeError(f"{info.field_name} is returning an non-boolean value: {value}")
        return bool(value)
    
    @field_validator('song_name', 'artist_name')
    def validate_names(cls, value, info):
        if type(value) is not str:
            raise TypeError(f"{info.field_name} must be a string: {type(value)}")
        if len(value.strip())==0:
            raise ValueError(f"{info.field_name} cannot be an empty string")
        return value.strip().lower()

    @field_validator('song_id', 'artist_id')
    def validate_ids(cls, value, info):
        '''Validate id fields'''
        if type(value) is not str:
            raise TypeError(f"{info.field_name} must be a string: {type(value)}")
        stripped=value.strip()
        if len(stripped)==0:
            raise ValueError(f'{info.field_name} cannot only contain whitespace or be an empty string: {value}')
        base62=string.digits + string.ascii_letters
        if not all(c in base62 for c in stripped):
            raise ValueError(f"{info.field_name} has invalid characters: {value}")
        return stripped
    
    @field_validator('song_url')
    def validate_url(cls, value, info):
        '''Ensure the url is a string and starts with https:// or http://'''
        if type(value) is not str:
            raise TypeError(f"{info.field_name} must be a string but this is type {type(value)}")
        if not value.strip().startswith('https://') and not value.strip().startswith('http://'):
            raise ValueError(f"{info.field_name} must start with https:// or http://")
        return value.strip()
    
    @field_validator('mbid')
    def validate_mbid(cls, value, info):
        '''Ensure the mbid is present, is a string, and matches the mbid pattern'''
        if type(value) is not str:
            raise TypeError(f"{info.field_name} must be a string but this is type {type(value)}")
        pattern= r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        if not re.match(pattern, value.lower().strip()):
            raise ValueError(f'{info.field_name} must match the mbid pattern')
        return value.strip().lower()
    
    



        

'''

    #calculated values
    @model_validator(mode='after')
    def check_calculations(cls, model):
        "Ensure calculated values are calulcated correctly"
        errors=[]
        if model.artist_total_listeners is not None and model.artist_total_playcount is not None and model.plays_per_listener is not None:
            calculated_ppl = round(model.artist_total_playcount/model.artist_total_listeners,5)
            if calculated_ppl != model.plays_per_listener:
                errors.append(f"plays_per_listener was calculated incorrectly: plays_per_listeners={model.plays_per_listener}, calculated_ppl={calculated_ppl}")
        
        if model.engagement_ratio is not None and model.artist_total_listeners is not None and model.num_song_listeners is not None:
            calculated_er = round(model.num_song_listeners/model.artist_total_listeners,5)
            if calculated_er != model.engagement_ratio:
                errors.append(f"engagement_ratio was calculated incorrectly: engagement_ratio={model.engagement_ratio}, calculated_er={calculated_er}")
        
        if errors:
            raise ValueError("; ".join(errors))
        
        return model

'''