from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import os

from schemas.song import SongResponse
from services.ytm_service import YTMService
from services.stream_service import StreamService

router = APIRouter(tags=["songs"])
stream_service = StreamService()

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
        stream_url = await stream_service.get_stream_url(song_id)
        
        if stream_url:
            return {"stream_url": stream_url}
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "Stream URL not available",
                    "message": "Could not extract stream URL for this video. This might be due to region restrictions, age restrictions, or the video being private/deleted.",
                    "video_id": song_id,
                    "suggestions": [
                        "Try using a different video ID",
                        "Check if the video is publicly accessible",
                        "Consider adding YouTube cookies for better access"
                    ]
                }
            )
            
    except Exception as e:
        error_message = str(e)
        
        # Provide more specific error messages based on the error type
        if "Sign in to confirm you're not a bot" in error_message:
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Bot detection",
                    "message": "YouTube detected automated access and requires authentication.",
                    "video_id": song_id,
                    "suggestions": [
                        "Add YouTube cookies to bypass bot detection",
                        "Use the /song/{song_id}/formats endpoint to check available formats",
                        "Try again later when YouTube's bot detection is less strict"
                    ]
                }
            )
        elif "Video unavailable" in error_message or "Private video" in error_message:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "Video unavailable",
                    "message": "The requested video is not available for streaming.",
                    "video_id": song_id,
                    "suggestions": [
                        "Check if the video ID is correct",
                        "Verify the video is publicly accessible",
                        "Try a different video"
                    ]
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": f"An error occurred while processing the request: {error_message}",
                    "video_id": song_id,
                    "suggestions": [
                        "Try again later",
                        "Check the video ID",
                        "Contact support if the issue persists"
                    ]
                }
            )

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

@router.get("/song/{song_id}/test")
async def test_song_access(song_id: str):
    """
    Test if a song is accessible and get basic info
    """
    try:
        stream_service = StreamService()
        test_result = await stream_service.test_video_accessibility(song_id)
        return test_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/stream")
async def test_stream_health():
    """
    Test stream service health with a known working video
    """
    try:
        stream_service = StreamService()
        
        # Test with a known working video (Rick Astley - Never Gonna Give You Up)
        test_video_id = "dQw4w9WgXcQ"
        
        # Test video accessibility
        test_result = await stream_service.test_video_accessibility(test_video_id)
        
        # Test stream URL extraction
        stream_url = await stream_service.get_stream_url(test_video_id)
        
        return {
            "status": "healthy" if test_result.get('accessible') and stream_url else "degraded",
            "video_test": test_result,
            "stream_test": {
                "success": bool(stream_url),
                "has_url": bool(stream_url)
            },
            "cookie_status": {
                "cookie_file_exists": os.path.exists(stream_service.cookie_file),
                "cookie_file_path": stream_service.cookie_file
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "cookie_status": {
                "cookie_file_exists": os.path.exists("cookies.txt"),
                "cookie_file_path": "cookies.txt"
            }
        }

 