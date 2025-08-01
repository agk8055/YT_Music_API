from fastapi import APIRouter, HTTPException

from schemas.playlist import PlaylistResponse
from services.ytm_service import YTMService

router = APIRouter(tags=["playlists"])

@router.get("/playlist/{playlist_id}", response_model=PlaylistResponse)
async def get_playlist(playlist_id: str):
    """
    Get playlist details by ID
    """
    try:
        ytm_service = YTMService()
        playlist = await ytm_service.get_playlist(playlist_id)
        return PlaylistResponse(playlist=playlist)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 