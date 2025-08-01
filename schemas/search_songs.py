from pydantic import BaseModel
from typing import List
from .song import Song

class SongSearchResult(BaseModel):
    type: str
    data: Song

class SongSearchResponse(BaseModel):
    results: List[SongSearchResult] 