from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, RedirectResponse
import httpx
import asyncio
import time
import logging
from contextlib import asynccontextmanager
import json

from api import search, songs, albums, playlists, artists, top_songs
from config import settings
from services.stream_service import StreamService
from services.background_task import background_task
from services.cache_service import cache_service

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
    # Start the background task
    background_task.start()
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
# For production, it's recommended to restrict the origins to a specific list of trusted domains
# Example: allow_origins=["https://your-frontend-domain.com"]
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

async def sse_generator(song_id: str, request: Request):
    # Add the song to the queue if it's not already being processed
    if not cache_service.get(song_id):
        background_task.add_song_to_queue(song_id)
        cache_service.set(song_id, {'status': 'pending'})

    # Wait for the stream to be ready
    while True:
        cached_item = cache_service.get(song_id)
        if cached_item and cached_item.get('status') == 'ready':
            stream_url = cached_item['url']
            break
        elif cached_item and cached_item.get('status') == 'failed':
            logger.error(f"Failed to get stream URL for {song_id}")
            return

        await asyncio.sleep(1)

    # Stream the audio
    http_client = request.app.state.http_client
    headers = {"Range": request.headers.get("range")} if "range" in request.headers else {}
    async with http_client.stream("GET", stream_url, headers=headers) as response:
        if response.status_code not in [200, 206]:
            logger.error(f"Failed to fetch stream for {song_id}. Status: {response.status_code}")
            return
        
        async for chunk in response.aiter_bytes():
            yield chunk


@app.get("/proxy-stream/{song_id}")
async def proxy_stream(
    request: Request,
    song_id: str,
):
    """
    Handles the streaming request.
    It establishes an SSE connection to wait for the stream URL to be ready,
    and then it streams the audio data directly.
    """
    if not song_id or len(song_id) != 11:
        raise HTTPException(status_code=400, detail="Invalid song ID format.")

    return StreamingResponse(sse_generator(song_id, request), media_type="audio/mpeg")


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
    """
    Returns the status of a stream preparation.
    """
    if not song_id or len(song_id) != 11:
        raise HTTPException(status_code=400, detail="Invalid song ID format.")

    cached_item = cache_service.get(song_id)

    if cached_item and cached_item.get('status') == 'ready':
        return {"status": "ready"}
    
    elif cached_item and cached_item.get('status') == 'pending':
        return {"status": "pending"}

    else:
        background_task.add_song_to_queue(song_id)
        cache_service.set(song_id, {'status': 'pending'})
        return {"status": "pending"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
