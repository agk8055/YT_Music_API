from pydantic import BaseModel
from typing import List

class SearchSuggestionsResponse(BaseModel):
    suggestions: List[str] 