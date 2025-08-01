from pydantic import BaseModel
from typing import List, Optional
from .common import Thumbnail
from .song import Song

class Playlist(BaseModel):
    id: Optional[str] = None  # Made optional to handle None values
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    track_count: Optional[str] = None  # Changed to str to handle "423K" format
    thumbnails: Optional[List[Thumbnail]] = None
    songs: Optional[List[Song]] = None

class PlaylistResponse(BaseModel):
    playlist: Playlist 