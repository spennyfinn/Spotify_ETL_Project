
from pydantic import ValidationError, BaseModel, Field, field_validator, model_validator
import math

class audio_features(BaseModel):
    song_name: str
    artist_id: str
    bpm: float
    energy: float
    spectral_centroid: float
    zero_crossing_rate: float
    danceability: float
    preview_url: str
    harmonic_ratio:float
    percussive_ratio:float


    @field_validator('energy', 'zero_crossing_rate', 'danceability', 'harmonic_ratio', 'percussive_ratio')
    def validate_zero_to_one(cls, value, info):
        if  not isinstance(value, float):
            raise TypeError(f'{info.field_name} should be of type float but is of type: {type(value)}')
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f'{info.field_name} cannot be NaN or Infinity')
        if value < 0 or value > 1:
                raise ValueError(f'{info.field_name} should be within the range of 0 and 1 but the value is: {value}')
        return float(value)
            

    @field_validator('song_name', 'artist_id')
    def ensure_string(cls, value, info):
        if isinstance(value, str ):
            return value.strip().lower()
        else:
            raise TypeError(f"{info.field_name} should be of type string but is of type: {type(value)}")

    @field_validator('bpm')
    def validate_bpm(cls, value, info):
        if not isinstance(value, float):
            raise TypeError(f"{info.field_name} should be of type float but is of type: {type(value)}")
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f'{info.field_name} cannot be NaN or Infinity')
        if value < 30 or value > 300:
            raise ValueError(f'{info.field_name} should be within range 30 - 300, but got: {value}')
        return float(value)

    @field_validator('spectral_centroid')
    def validate_spectral_centroid(cls, value, info):
        if not isinstance(value, float):
            raise TypeError(f"{info.field_name} should be of type float but is of type: {type(value)}")
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f'{info.field_name} cannot be NaN or Infinity')
        if value < 0 or value > 10000:
            raise ValueError(f'{info.field_name} should be between 0 and 10000 Hz, but recieved: {value}')
        return float(value)



    @field_validator('preview_url')
    def validate_url(cls, value, info):
        if not isinstance(value, str):
            raise TypeError(f"{info.field_name} should be of type string but is of type: {type(value)}")
        if not value.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        if not (value.strip().startswith('https://') or value.strip().startswith('http://')):
            raise ValueError(f"{info.field_name} should be a valid url starting with https:// or http://")
        return value.strip()

        

    @model_validator(mode='after')
    def validate_danceability(cls, model):
        tempo_normalized= min(model.bpm/200.0, 1.0)
        expected_danceability = round((tempo_normalized*.3)+ (model.energy * .5)+ (model.zero_crossing_rate*.2), 5)
        if abs(model.danceability - expected_danceability) > .0001:
            raise ValueError(
                f'Danceability calculation mismatch: '
                f'Expexted Danceability: {expected_danceability}, recieved {model.danceability}')
        return model








