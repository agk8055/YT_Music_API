from pydantic import BaseModel
from typing import Optional

class Thumbnail(BaseModel):
    url: str
    width: Optional[int] = None
    height: Optional[int] = None 