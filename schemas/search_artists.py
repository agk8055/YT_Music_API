from pydantic import BaseModel
from typing import List
from .artist import Artist

class ArtistSearchResult(BaseModel):
    type: str
    data: Artist

class ArtistSearchResponse(BaseModel):
    results: List[ArtistSearchResult] 