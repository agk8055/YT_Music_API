from fastapi import APIRouter, HTTPException

from schemas.song import SongResponse
from services.ytm_service import YTMService
from services.stream_service import StreamService

router = APIRouter(tags=["songs"])

@router.get("/song/{song_id}", response_model=SongResponse)
async def get_song(song_id: str):
    """
    Get song details by ID
    """
    try:
        ytm_service = YTMService()
        song = await ytm_service.get_song(song_id)
        return SongResponse(song=song)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/song/{song_id}/stream")
async def get_song_stream(song_id: str):
    """
    Get stream URL for a song (optimized with caching and performance improvements)
    """
    try:
        stream_service = StreamService()
        stream_url = await stream_service.get_stream_url(song_id)
        return {"stream_url": stream_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/song/{song_id}/formats")
async def get_song_formats(song_id: str):
    """
    Get all available audio formats for a song
    """
    try:
        stream_service = StreamService()
        formats = await stream_service.get_available_formats(song_id)
        return {"formats": formats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/song/{song_id}/direct-formats")
async def get_song_direct_formats(song_id: str):
    """
    Get only direct audio formats (excluding HLS playlists) for a song
    """
    try:
        stream_service = StreamService()
        formats = await stream_service.get_direct_audio_formats(song_id)
        return {"direct_formats": formats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

 