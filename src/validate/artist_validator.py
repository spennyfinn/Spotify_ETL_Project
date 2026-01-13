
import string
from pydantic import BaseModel, field_validator, model_validator
import math
from typing import Any

class ArtistData(BaseModel):
    artist_id: Any
    popularity: Any
    followers: Any
    genres: Any
    has_genres: Any
    genre_count: Any
    source: Any



    @field_validator('artist_id')
    def validate_id(cls, v, info):
        if type(v) is not str:
            raise TypeError(f'{info.field_name} must be a string but it was {type(v)}')
        id = v.strip()
        if id == '' or len(id)==0:
            raise ValueError(f"An artist id cannot be 0 or an empty string")
        if len(id)!=22:
            raise ValueError("An artist id must be 22 char long")
        base62 = string.ascii_letters + string.digits
        if not all(char in base62 for char in id):
            raise ValueError(f"{info.field_name} contains characters that aren't allowed in Spotify IDs")
        return id

    @field_validator('popularity')
    def validate_popularity(cls, v, info):
        if type(v) is not int:
            raise TypeError(f'{info.field_name} must be an integer but it was {type(v)}')
        if v<0 or v>100:
            raise ValueError(f'{info.field_name} represents a percentage, so it must be between 0 and 100 (got {v})')
        return int(v)


    @field_validator('followers')
    def validate_followers(cls, v, info):
        if type(v) is not int:
            raise TypeError(f'{info.field_name} must be an integer but it was {type(v)}')
        if v<0:
            raise ValueError(f'{info.field_name} must be above 0  (got {v})')
        return int(v)
    
    @field_validator('source')
    def validate_source(cls, v, info):
        if type(v) is not str:
            raise TypeError(f'{info.field_name} must be a string but it was {type(v)}')
        stripped= v.strip()
        if stripped!='spotify':
            raise ValueError(f'{info.field_name} must be "spotify"')
        return str(stripped)

    @field_validator('genres')
    def validate_genre(cls, v ,info):
        if type(v) is not list:
            raise TypeError(f'{info.field_name} must be a list but it was {type(v)}')
        if len(v)>5:
            v= v[:5]
            return v
        return v
    
    @field_validator('genres')
    def validate_genre_strings(cls, v, info):
        validated_genres=[]

        for i, genre in enumerate(v):
            if type(genre) is not str:
                raise TypeError(f'Genre at index {i} must be a string but it was {type(v)}')
            cleaned_genre= genre.strip().lower()

            if not cleaned_genre:
                raise ValueError(f'Genre at index {i} cannot be empty')
            if len(cleaned_genre) < 2:
                raise ValueError(f'Genre "{cleaned_genre}" too short (min 2 chars)')
            if len(cleaned_genre) > 50:
                raise ValueError(f'Genre "{cleaned_genre}" too long (max 50 chars)')
            
            validated_genres.append(cleaned_genre)
        unique_genres= []
        seen = set()
        for genre in validated_genres:
            genre= genre.lower().strip()
            if genre not in seen:
                seen.add(genre)
                unique_genres.append(genre)
        return unique_genres
        




    
