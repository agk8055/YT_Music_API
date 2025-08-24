from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
import asyncio

from api import search, songs, albums, playlists, artists, top_songs
from config import settings

app = FastAPI(
    title="YT Music API",
    description="A FastAPI-based REST API for YouTube Music data and streaming",
    version="1.0.0"
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
    song_id: str,
    format: str = "bestaudio",
    quality: str = "best",
    range: str = None
):
    """
    Proxy stream for a song - gets stream URL from /song/{song_id}/stream and proxies the audio
    
    Args:
        song_id: YouTube video ID
        format: Audio format preference (default: "bestaudio")
        quality: Quality preference (default: "best")
        range: HTTP Range header value for seeking support (e.g., "bytes=0-")
    """
    try:
        # Validate song_id format (YouTube video IDs are typically 11 characters)
        if not song_id or len(song_id) != 11:
            raise HTTPException(status_code=400, detail="Invalid song ID format. YouTube video IDs must be 11 characters.")
        
        # Get the stream URL directly from the stream service
        from services.stream_service import StreamService
        stream_service = StreamService()
        
        # Get the stream URL with timeout
        try:
            stream_url = await asyncio.wait_for(
                stream_service.get_stream_url(song_id),
                timeout=90.0
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="Request timeout while getting stream URL")
        
        if not stream_url:
            raise HTTPException(status_code=404, detail="Stream URL not available")
        
        # Now proxy the stream to the client
        async def stream_audio():
            headers = {}
            if range:
                headers["Range"] = range
            
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
                async with client.stream("GET", stream_url, headers=headers) as response:
                    if response.status_code not in [200, 206]:  # 206 is Partial Content for range requests
                        raise HTTPException(status_code=response.status_code, detail="Failed to fetch stream")
                    
                    # Stream the audio data chunk by chunk
                    async for chunk in response.aiter_bytes():
                        yield chunk
        
        # Return streaming response with appropriate headers
        response_headers = {
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Range, Content-Type",
            "Access-Control-Expose-Headers": "Content-Length, Content-Range, Accept-Ranges"
        }
        
        # Add content length if range request
        if range and range.startswith("bytes="):
            try:
                # Parse range to get start and end
                range_parts = range.replace("bytes=", "").split("-")
                if len(range_parts) == 2 and range_parts[1]:
                    start = int(range_parts[0])
                    end = int(range_parts[1])
                    content_length = end - start + 1
                    response_headers["Content-Length"] = str(content_length)
                    response_headers["Content-Range"] = f"bytes {start}-{end}/*"
            except (ValueError, IndexError):
                pass  # Invalid range format, continue without content length
        
        return StreamingResponse(
            stream_audio(),
            media_type="audio/mpeg",
            headers=response_headers
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
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
async def proxy_stream_head(song_id: str):
    """
    Get metadata for a song stream without downloading the audio
    """
    try:
        # Validate song_id format
        if not song_id or len(song_id) != 11:
            raise HTTPException(status_code=400, detail="Invalid song ID format. YouTube video IDs must be 11 characters.")
        
        # Get the stream URL to verify it exists
        from services.stream_service import StreamService
        stream_service = StreamService()
        
        try:
            stream_url = await asyncio.wait_for(
                stream_service.get_stream_url(song_id),
                timeout=30.0  # Shorter timeout for HEAD requests
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