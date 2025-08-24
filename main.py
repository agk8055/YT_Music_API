from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
import asyncio
import time
import logging
from contextlib import asynccontextmanager

from api import search, songs, albums, playlists, artists, top_songs
from config import settings
from services.stream_service import StreamService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a lifespan context manager for application startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize and store a single, reusable httpx.AsyncClient
    app.state.http_client = httpx.AsyncClient(timeout=httpx.Timeout(120.0))
    # Initialize and store a single, reusable StreamService
    app.state.stream_service = StreamService()
    yield
    # Clean up the httpx.AsyncClient on application shutdown
    await app.state.http_client.aclose()

app = FastAPI(
    title="YT Music API",
    description="A FastAPI-based REST API for YouTube Music data and streaming",
    version="1.0.0",
    lifespan=lifespan  # Use the lifespan context manager
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router, prefix=settings.API_PREFIX)
app.include_router(songs.router, prefix=settings.API_PREFIX)
app.include_router(albums.router, prefix=settings.API_PREFIX)
app.include_router(playlists.router, prefix=settings.API_PREFIX)
app.include_router(artists.router, prefix=settings.API_PREFIX)
app.include_router(top_songs.router, prefix=settings.API_PREFIX)

@app.get("/")
async def root():
    return {"message": "Welcome to YT Music API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/proxy-stream/{song_id}")
async def proxy_stream(
    request: Request,
    song_id: str,
    format: str = "bestaudio",
    quality: str = "best"
):
    """
    Proxy stream for a song - gets stream URL from /song/{song_id}/stream and proxies the audio
    """
    start_time = time.time()
    try:
        if not song_id or len(song_id) != 11:
            raise HTTPException(status_code=400, detail="Invalid song ID format.")

        stream_service = request.app.state.stream_service
        
        get_url_start_time = time.time()
        try:
            stream_url = await asyncio.wait_for(
                stream_service.get_stream_url(song_id),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"Timeout getting stream URL for song_id: {song_id}")
            raise HTTPException(status_code=408, detail="Request timeout while getting stream URL")
        finally:
            get_url_duration = time.time() - get_url_start_time
            logger.info(f"Getting stream URL for {song_id} took {get_url_duration:.2f} seconds.")

        if not stream_url:
            raise HTTPException(status_code=404, detail="Stream URL not available")

        http_client = request.app.state.http_client

        async def stream_audio():
            headers = {"Range": request.headers.get("range")} if "range" in request.headers else {}
            first_byte_time = None
            
            async with http_client.stream("GET", stream_url, headers=headers) as response:
                if response.status_code not in [200, 206]:
                    raise HTTPException(status_code=response.status_code, detail="Failed to fetch stream")
                
                async for chunk in response.aiter_bytes():
                    if first_byte_time is None:
                        first_byte_time = time.time()
                        first_byte_duration = first_byte_time - get_url_start_time
                        logger.info(f"Time to first byte for {song_id}: {first_byte_duration:.2f} seconds.")
                    yield chunk

        response_headers = {
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
            "Access-Control-Expose-Headers": "Content-Length, Content-Range, Accept-Ranges"
        }

        return StreamingResponse(
            stream_audio(),
            media_type="audio/mpeg",
            headers=response_headers
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in proxy_stream for {song_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        total_duration = time.time() - start_time
        logger.info(f"Total request time for {song_id}: {total_duration:.2f} seconds.")


@app.options("/proxy-stream/{song_id}")
async def proxy_stream_options(song_id: str):
    return {
        "message": "CORS preflight response",
        "allowed_methods": ["GET", "HEAD", "OPTIONS"],
        "allowed_headers": ["Range", "Content-Type"],
        "exposed_headers": ["Content-Length", "Content-Range", "Accept-Ranges"]
    }


@app.head("/proxy-stream/{song_id}")
async def proxy_stream_head(request: Request, song_id: str):
    try:
        if not song_id or len(song_id) != 11:
            raise HTTPException(status_code=400, detail="Invalid song ID format.")

        stream_service = request.app.state.stream_service
        
        try:
            stream_url = await asyncio.wait_for(
                stream_service.get_stream_url(song_id),
                timeout=20.0
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="Request timeout while getting stream URL")

        if not stream_url:
            raise HTTPException(status_code=404, detail="Stream URL not available")

        return {
            "status": "available",
            "song_id": song_id,
            "stream_url_exists": True,
            "accept_ranges": "bytes",
            "content_type": "audio/mpeg"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)