from pydantic import BaseModel
from typing import List
from .playlist import Playlist

class PlaylistSearchResult(BaseModel):
    type: str
    data: Playlist

class PlaylistSearchResponse(BaseModel):
    results: List[PlaylistSearchResult] 