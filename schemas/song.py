from pydantic import BaseModel
from typing import List, Optional
from .common import Thumbnail

class Song(BaseModel):
    id: Optional[str] = None  # Made optional to handle None values
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[str] = None
    thumbnails: Optional[List[Thumbnail]] = None
    url: Optional[str] = None
    stream_url: Optional[str] = None  # Added stream URL field

class SongResponse(BaseModel):
    song: Song 