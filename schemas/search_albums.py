from pydantic import BaseModel
from typing import List
from .album import Album

class AlbumSearchResult(BaseModel):
    type: str
    data: Album

class AlbumSearchResponse(BaseModel):
    results: List[AlbumSearchResult] 