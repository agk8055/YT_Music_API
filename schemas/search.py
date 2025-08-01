from pydantic import BaseModel
from typing import List, Union
from .song import Song
from .album import Album
from .playlist import Playlist
from .artist import Artist

class SearchResult(BaseModel):
    type: str
    data: Union[Song, Album, Playlist, Artist]

class SearchResponse(BaseModel):
    results: List[SearchResult] 