from fastapi import APIRouter, HTTPException

from schemas.artist import ArtistResponse, ArtistSongsResponse, ArtistPlaylistsResponse, ArtistAlbumsResponse
from services.ytm_service import YTMService

router = APIRouter(tags=["artists"])

@router.get("/artist/{artist_id}", response_model=ArtistResponse)
async def get_artist(artist_id: str):
    """
    Get artist details by ID
    """
    try:
        ytm_service = YTMService()
        artist = await ytm_service.get_artist(artist_id)
        return ArtistResponse(artist=artist)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/artist/{artist_id}/songs", response_model=ArtistSongsResponse)
async def get_artist_songs(artist_id: str):
    """
    Get artist's songs by artist ID
    """
    try:
        ytm_service = YTMService()
        songs = await ytm_service.get_artist_songs(artist_id)
        return ArtistSongsResponse(songs=songs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/artist/{artist_id}/playlists", response_model=ArtistPlaylistsResponse)
async def get_artist_playlists(artist_id: str):
    """
    Get artist's playlists by artist ID
    """
    try:
        ytm_service = YTMService()
        playlists = await ytm_service.get_artist_playlists(artist_id)
        return ArtistPlaylistsResponse(playlists=playlists)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/artist/{artist_id}/albums", response_model=ArtistAlbumsResponse)
async def get_artist_albums(artist_id: str):
    """
    Get artist's albums by artist ID, sorted by release date (latest first)
    """
    try:
        ytm_service = YTMService()
        albums = await ytm_service.get_artist_albums(artist_id)
        return ArtistAlbumsResponse(albums=albums)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 