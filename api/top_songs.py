from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from schemas.top_songs import TopSongsResponse
from services.ytm_service import YTMService

router = APIRouter(tags=["top songs"])

@router.get("/top-songs", response_model=TopSongsResponse)
async def get_top_songs(
    region: Optional[str] = Query(None, description="Country/region code (e.g., 'US', 'IN', 'GB'). Leave empty for global top songs"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of songs to return (1-50)")
):
    """
    Get top latest songs globally or for a specific country/region.
    
    - **region**: Optional country/region code (e.g., 'US', 'IN', 'GB'). If not provided, returns global top songs
    - **limit**: Maximum number of songs to return (1-50, default: 20)
    """
    try:
        ytm_service = YTMService()
        songs = await ytm_service.get_top_songs(region=region, limit=limit)
        
        return TopSongsResponse(
            songs=songs,
            region=region,
            total_count=len(songs),
            message=f"Top {len(songs)} songs {'for ' + region if region else 'globally'}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-songs/global", response_model=TopSongsResponse)
async def get_global_top_songs(
    limit: int = Query(20, ge=1, le=50, description="Maximum number of songs to return (1-50)")
):
    """
    Get global top latest songs.
    
    - **limit**: Maximum number of songs to return (1-50, default: 20)
    """
    try:
        ytm_service = YTMService()
        songs = await ytm_service.get_top_songs(region=None, limit=limit)
        
        return TopSongsResponse(
            songs=songs,
            region="global",
            total_count=len(songs),
            message=f"Top {len(songs)} global songs"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-songs/country/{country_code}", response_model=TopSongsResponse)
async def get_country_top_songs(
    country_code: str,
    limit: int = Query(20, ge=1, le=50, description="Maximum number of songs to return (1-50)")
):
    """
    Get top latest songs for a specific country.
    
    - **country_code**: Country code (e.g., 'US', 'IN', 'GB', 'CA', 'AU')
    - **limit**: Maximum number of songs to return (1-50, default: 20)
    """
    try:
        ytm_service = YTMService()
        songs = await ytm_service.get_top_songs(region=country_code.upper(), limit=limit)
        
        return TopSongsResponse(
            songs=songs,
            region=country_code.upper(),
            total_count=len(songs),
            message=f"Top {len(songs)} songs for {country_code.upper()}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 