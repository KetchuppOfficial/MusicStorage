"""Schemas"""

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    """Schema for user creation"""

    username: str
    password: str


class SongCreate(BaseModel):
    """Schema for song creation"""

    title: str
    genre: str
    rating: int
    artist_id: int


class SongOut(BaseModel):
    """Schema for song deletion"""

    id: int
    title: str
    genre: str
    rating: int
    model_config = ConfigDict(from_attributes=True)
