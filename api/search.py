from fastapi import APIRouter, HTTPException
from typing import Optional

from schemas.search import SearchResponse
from schemas.search_songs import SongSearchResponse
from schemas.search_albums import AlbumSearchResponse
from schemas.search_artists import ArtistSearchResponse
from schemas.search_playlists import PlaylistSearchResponse
from services.ytm_service import YTMService

router = APIRouter(tags=["search"])

@router.get("/search", response_model=SearchResponse)
async def search_content(
    query: str,
    limit: Optional[int] = 20,
    include_stream_urls: Optional[bool] = False
):
    """
    Global search across songs, albums, playlists, and artists
    """
    try:
        ytm_service = YTMService()
        results = await ytm_service.search(query, limit, include_stream_urls)
        return SearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/songs", response_model=SongSearchResponse)
async def search_songs(
    query: str,
    limit: Optional[int] = 20,
    include_stream_urls: Optional[bool] = False
):
    """
    Search for songs only
    """
    try:
        ytm_service = YTMService()
        results = await ytm_service.search_songs(query, limit, include_stream_urls)
        return SongSearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/albums", response_model=AlbumSearchResponse)
async def search_albums(
    query: str,
    limit: Optional[int] = 20
):
    """
    Search for albums only
    """
    try:
        ytm_service = YTMService()
        results = await ytm_service.search_albums(query, limit)
        return AlbumSearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/artists", response_model=ArtistSearchResponse)
async def search_artists(
    query: str,
    limit: Optional[int] = 20
):
    """
    Search for artists only
    """
    try:
        ytm_service = YTMService()
        results = await ytm_service.search_artists(query, limit)
        return ArtistSearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/playlists", response_model=PlaylistSearchResponse)
async def search_playlists(
    query: str,
    limit: Optional[int] = 20
):
    """
    Search for playlists only
    """
    try:
        ytm_service = YTMService()
        results = await ytm_service.search_playlists(query, limit)
        return PlaylistSearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 