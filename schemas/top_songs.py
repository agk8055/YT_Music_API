from pydantic import BaseModel
from typing import List, Optional
from .song import Song

class TopSongsResponse(BaseModel):
    songs: List[Song]
    region: Optional[str] = None
    total_count: int
    message: Optional[str] = None 