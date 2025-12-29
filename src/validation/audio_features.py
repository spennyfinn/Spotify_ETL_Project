
import string
from pydantic import BaseModel, field_validator, model_validator
import math
from typing import Any

class AudioFeatures(BaseModel):
    song_id: Any
    bpm: Any
    energy: Any
    spectral_centroid: Any
    zero_crossing_rate: Any
    danceability: Any
    preview_url: Any
    harmonic_ratio:Any
    percussive_ratio:Any
    source: str



    @field_validator('energy', 'zero_crossing_rate', 'danceability', 'harmonic_ratio', 'percussive_ratio')
    def validate_zero_to_one(cls, value, info):
        if type(value) is not float:
            raise TypeError(f'{info.field_name} should be of type float but is of type: {type(value)}')
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f'{info.field_name} cannot be NaN or Infinity')
        if value < 0 or value > 1:
                raise ValueError(f'{info.field_name} should be within the range of 0 and 1 but the value is: {value}')
        return float(value)
        

    @field_validator('song_id')
    def validate_ids(cls, value, info):
        if type(value) is not str:
            raise TypeError(f'{info.field_name} should be of type str but is of type: {type(value)}')
        stripped= value.strip()
        if len(value)!=22:
            raise ValueError(f'{info.field_name} should be exactly 22 characters but received: {len(stripped)} chars')
        base64= string.ascii_letters+string.digits
        if not all(c in base64 for c in stripped):
            raise ValueError(f'{info.field_name} should only contain base64 characters: {value}')
        return stripped

    @field_validator('bpm')
    def validate_bpm(cls, value, info):
        if type(value) is not float:
            raise TypeError(f'{info.field_name} should be of type float but is of type: {type(value)}')
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f'{info.field_name} cannot be NaN or Infinity')
        if value < 0 or value > 300:
            raise ValueError(f'{info.field_name} should be within range 30 - 300, but got: {value}')
        return float(value)

    @field_validator('spectral_centroid')
    def validate_spectral_centroid(cls, value, info):
        if type(value) is not float:
            raise TypeError(f'{info.field_name} should be of type float but is of type: {type(value)}')
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f'{info.field_name} cannot be NaN or Infinity')
        if value < 0 or value > 10000:
            raise ValueError(f'{info.field_name} should be between 0 and 10000 Hz, but recieved: {value}')
        return float(value)



    @field_validator('preview_url')
    def validate_url(cls, value, info):
        if type(value) is not str:
            raise TypeError(f'{info.field_name} should be of type str but is of type: {type(value)}')
        stripped= value.strip()
        if len(stripped)==0:
            raise ValueError(f"{info.field_name} cannot be empty")
        if not (stripped.startswith('https://') or stripped.startswith('http://')):
            raise ValueError(f"{info.field_name} should be a valid url starting with https:// or http://")
        return stripped



        

    @model_validator(mode='after')
    def validate_danceability(cls, model):
        tempo_normalized= min(model.bpm/200.0, 1.0)
        expected_danceability = round((tempo_normalized*.3)+ (model.energy * .5)+ (model.zero_crossing_rate*.2), 5)
        if abs(model.danceability - expected_danceability) > .0001:
            raise ValueError(
                f'Danceability calculation mismatch: '
                f'Expexted Danceability: {expected_danceability}, recieved {model.danceability}')
        return model
    










