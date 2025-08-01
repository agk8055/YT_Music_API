from pydantic import BaseModel
from typing import List, Optional
from .common import Thumbnail
from .song import Song

class Album(BaseModel):
    id: Optional[str] = None  # Made optional to handle None values
    title: str
    artist: str
    year: Optional[int] = None
    track_count: Optional[str] = None  # Changed to str to handle "423K" format
    thumbnails: Optional[List[Thumbnail]] = None
    songs: Optional[List[Song]] = None

class AlbumResponse(BaseModel):
    album: Album 