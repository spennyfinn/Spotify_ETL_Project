from pydantic import ValidationError, BaseModel, Field, field_validator, model_validator
from typing import List



class Last_fm_data(BaseModel):
    song_name: str
    artist_name: str
    rank: int
    duration_seconds: int
    duration_minutes: float
    num_song_listeners:int
    song_id: str
    song_url: str
    artist_id:str
    artist_url:str
    album_title:str
    tags: List[str]
    similar_artists: List[str]
    on_tour: int  
    artist_total_playcount: int
    artist_total_listeners: int
    plays_per_listener: float
    engagement_ratio:float

    # Ensures that numerical valuesa are non negative
    @field_validator('rank', 'duration_minutes', 'duration_seconds', 'num_song_listeners', 'artist_total_playcount', 'artist_total_listeners', 'plays_per_listener', 'engagement_ratio')
    def non_negative_num(cls, value, info):
        if value<0:
            raise ValueError(f"{info.field_name} has a negative value when it shouldn't: {value}")
        elif value ==0:
            raise ValueError(f"{info.field_name} is 0 when it shouldn't: {value}")
        return value
        
    # Ensures that boolean columns only have values of 0/1
    @field_validator('on_tour')
    def validate_boolean_numbers(cls, value, info):
        if value!= 1 and value!=0:
            raise ValueError(f"{info.field_name} is returning an non-boolean int: {value}")
        return value
    

    
    #calculated values
    @model_validator(mode='after')
    def check_calculations(cls, model):
        errors=[]

        if model.duration_seconds is not None and model.duration_minutes is not None:
            calculated_mins = round((model.duration_seconds/60),2)
            if calculated_mins != model.duration_minutes:
                errors.append(f"duration_minutes was calculated incorrectly: minutes={model.duration_minutes}, calculated_minutes={calculated_mins}")
        
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

