from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
import asyncio
from contextlib import asynccontextmanager

from api import search, songs, albums, playlists, artists, top_songs
from config import settings
from services.stream_service import StreamService

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
    
    Args:
        request: The incoming request object
        song_id: YouTube video ID
        format: Audio format preference (default: "bestaudio")
        quality: Quality preference (default: "best")
    """
    try:
        # Validate song_id format
        if not song_id or len(song_id) != 11:
            raise HTTPException(status_code=400, detail="Invalid song ID format. YouTube video IDs must be 11 characters.")
        
        # Use the shared StreamService instance
        stream_service = request.app.state.stream_service
        
        # Get the stream URL with a shorter timeout
        try:
            stream_url = await asyncio.wait_for(
                stream_service.get_stream_url(song_id),
                timeout=30.0  # Increased timeout
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="Request timeout while getting stream URL")
        
        if not stream_url:
            raise HTTPException(status_code=404, detail="Stream URL not available")
        
        # Use the shared httpx.AsyncClient for streaming
        http_client = request.app.state.http_client
        
        async def stream_audio():
            headers = {"Range": request.headers.get("range")} if "range" in request.headers else {}
            
            async with http_client.stream("GET", stream_url, headers=headers) as response:
                if response.status_code not in [200, 206]:
                    raise HTTPException(status_code=response.status_code, detail="Failed to fetch stream")
                
                async for chunk in response.aiter_bytes():
                    yield chunk
        
        # Simplified response headers
        response_headers = {
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
            "Access-Control-Expose-Headers": "Content-Length, Content-Range, Accept-Ranges"
        }

        # Let FastAPI handle Content-Length and Content-Range based on the stream
        return StreamingResponse(
            stream_audio(),
            media_type="audio/mpeg",
            headers=response_headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.options("/proxy-stream/{song_id}")
async def proxy_stream_options(song_id: str):
    """
    Handle CORS preflight requests for the proxy-stream endpoint
    """
    return {
        "message": "CORS preflight response",
        "allowed_methods": ["GET", "HEAD", "OPTIONS"],
        "allowed_headers": ["Range", "Content-Type"],
        "exposed_headers": ["Content-Length", "Content-Range", "Accept-Ranges"]
    }


@app.head("/proxy-stream/{song_id}")
async def proxy_stream_head(request: Request, song_id: str):
    """
    Get metadata for a song stream without downloading the audio
    """
    try:
        # Validate song_id format
        if not song_id or len(song_id) != 11:
            raise HTTPException(status_code=400, detail="Invalid song ID format. YouTube video IDs must be 11 characters.")
        
        # Use the shared StreamService instance
        stream_service = request.app.state.stream_service
        
        try:
            stream_url = await asyncio.wait_for(
                stream_service.get_stream_url(song_id),
                timeout=20.0  # Increased timeout for HEAD requests
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="Request timeout while getting stream URL")
        
        if not stream_url:
            raise HTTPException(status_code=404, detail="Stream URL not available")
        
        # Return headers only
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