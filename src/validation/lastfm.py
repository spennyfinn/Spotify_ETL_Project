from typing import Optional
from numba import bool_
from pydantic import  BaseModel, field_validator, model_validator
import re



class Last_fm_data(BaseModel):
    song_name: str
    artist_name: str
    num_song_listeners: int
    song_url: Optional[str] = None
    mbid: Optional[str]= None
    on_tour: Optional[bool]= None 
    song_id: Optional[str] = None
    artist_total_playcount: int
    artist_total_listeners: int
    plays_per_listener: float
    engagement_ratio:float
    artist_id: str


    @model_validator(mode='before')
    def validate_required_fields(cls, values):
        '''Ensure required fields are present'''
        required_fields=['song_name', 'artist_name', 'artist_id']
        missing = [field for field in required_fields if values[field] is None or field not in values]
        if missing:
            raise ValueError(f'Missing required fields {', '.join(missing)}')
        return values

    # Ensures that numerical values are non negative
    @field_validator('num_song_listeners', 'artist_total_playcount', 'artist_total_listeners', 'plays_per_listener', 'engagement_ratio')
    def non_negative_num(cls, value, info):
        """Ensure these values are numerical and greater than 0"""
        if not isinstance(value, (int, float)):
            raise TypeError(f'{info.field_name} is supposed to be a numerical value but is: {type(value)}')
        if value<0:
            raise ValueError(f"{info.field_name} has a negative value when it shouldn't: {value}")
        elif value ==0:
            raise ValueError(f"{info.field_name} is 0 when it shouldn't be: {value}")
        return int(value) if isinstance(value, int) else float(value)
        
    # Ensures that boolean columns only have values of 0/1
    @field_validator('on_tour')
    def validate_on_tour(cls, value, info):
        '''Ensure the on_tour values are boolean'''
        if not isinstance(value, bool):
            raise ValueError(f"{info.field_name} is returning an non-boolean value: {value}")
        return bool(value)
    
    @field_validator('song_name', 'artist_name', 'artist_id')
    def validate_required_strings(cls, value, info):
        '''Validate required string fields'''
        if not value:
            raise ValueError(f"{info.field_name} cannot be None")
        if not isinstance(value, str):
            raise TypeError(f"{info.field_name} must be of type string but it is a {type(value)} type")
        if len(value.strip())==0:
            raise ValueError(f"{info.field_name} cannot be an empty string")
        return value.strip().lower() if info.field_name in ['song_name', 'artist_name'] else value.strip()

    @field_validator('song_id', 'song_url', 'mbid')
    def validate_optional_strings(cls, value, info):
        '''Validate optional string fields'''
        if not value:
            return None
        if not isinstance(value, str):
            raise TypeError(f"{info.field_name} must be a string or None")
        return value.strip() 
    
    @field_validator('song_url')
    def validate_url(cls, value, info):
        '''Ensure the url is a string and starts with https:// or http://'''
        if not value or value=='':
            return None
        if not isinstance(value, str):
            raise TypeError(f"{info.field_name} must be a string but this is type {type(value)}")
        if not value.strip().startswith('https://') and not value.strip().startswith('http://'):
            raise ValueError(f"{info.field_name} must start with https:// or http://")
        return value.strip()
    
    @field_validator('mbid')
    def validate_mbid(cls, value, info):
        '''Ensure the mbid is present, is a string, and matches the mbid pattern'''
        if not value or value =='':
            return None
        if not isinstance(value, str):
            raise TypeError(f"{info.field_name} must be a string but this is type {type(value)}")
        pattern= r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        if not re.match(pattern, value.lower().strip()):
            raise ValueError(f'{info.field_name} must match the mbid pattern')
        return value.strip().lower()
    
    @field_validator('engagement_ratio')
    def validate_engagement_ratio(cls, value, info):
        """Ensure engagement_ratio is present, is a float, and is within the range(0,1)"""
        if not value:
            return None
        if not isinstance(value, float):
            raise TypeError(f'{info.field_name} must be type float but it is type {type(value)}')
        if value < 0:
            raise ValueError(f"{info.field_name} should be in greater than 0 but got {value}")
        return float(value)
    
    @field_validator('plays_per_listener')
    def validate_plays_per_listener(cls, value, info):
        """Ensure the plays_per_listener value is present, is a float, and is in the range(0,2000)"""
        if not value:
            return None
        if not isinstance(value, float):
            raise TypeError(f'{info.field_name} must be type float but it is type {type(value)}')
        if value < 0:
            raise ValueError(f"{info.field_name} should be positive but got {value}")
        if value > 2000:
            raise ValueError(f'{info.field_name} seems unreasonably high: {value}')
        return float(value)
        



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

