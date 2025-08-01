from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import search, songs, albums, playlists, artists
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

@app.get("/")
async def root():
    return {"message": "Welcome to YT Music API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 