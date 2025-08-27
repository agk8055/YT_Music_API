from fastapi import APIRouter, HTTPException

from schemas.album import AlbumResponse
from services.ytm_service import YTMService

router = APIRouter(tags=["albums"])
ytm_service = YTMService()

@router.get("/album/{album_id}", response_model=AlbumResponse)
async def get_album(album_id: str):
    """
    Get album details by ID
    """
    try:
        album = await ytm_service.get_album(album_id)
        return AlbumResponse(album=album)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 