# YT Music API

A FastAPI-based REST API for YouTube Music data and streaming.

## Features

- Search for songs, albums, artists, and playlists
- Stream music from YouTube Music
- RESTful API with comprehensive endpoints

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the development server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## Production Deployment

### Render Deployment

1. **Option 1: Using render.yaml (Recommended)**
   - Connect your GitHub repository to Render
   - Render will automatically detect the `render.yaml` file and deploy
   - No additional configuration needed

2. **Option 2: Manual Setup**
   - Create a new Web Service on Render
   - Set the following:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn main:app -c gunicorn.conf.py`
     - **Environment**: Python 3.11

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t yt-music-api .
```

2. Run the container:
```bash
docker run -p 8000:8000 yt-music-api
```

## Troubleshooting

### Stream URL Issues

If you're experiencing issues with stream URLs returning `null` or slow response times, try the following:

1. **Get stream URL (optimized):**
   ```bash
   curl "http://localhost:8000/song/{song_id}/stream"
   ```

2. **Check available formats:**
   ```bash
   curl "http://localhost:8000/song/{song_id}/formats"
   ```

3. **Get direct audio formats only:**
   ```bash
   curl "http://localhost:8000/song/{song_id}/direct-formats"
   ```



### Common Issues

- **403 Forbidden errors**: YouTube may block requests due to rate limiting. The service includes better headers and retry logic.
- **Format not available**: Some videos may not have the requested audio format. The service includes fallback mechanisms.
- **HLS playlists**: The service now filters out HLS playlists and returns direct audio URLs.
- **yt-dlp version**: Make sure you're using the latest version of yt-dlp (>=2024.3.10).

## API Endpoints

### Core Endpoints
- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /docs` - API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

### Search Endpoints
- `GET /search` - Global search across songs, albums, playlists, and artists
- `GET /search/songs` - Search for songs only
- `GET /search/albums` - Search for albums only
- `GET /search/artists` - Search for artists only
- `GET /search/playlists` - Search for playlists only
- `GET /search/suggestions` - Get search suggestions/autocomplete for a given keyword

### Content Endpoints
- `GET /songs/{song_id}` - Get song details by ID
- `GET /songs/{song_id}/stream` - Get stream URL for a song (optimized with caching)
- `GET /songs/{song_id}/formats` - Get all available audio formats for a song
- `GET /songs/{song_id}/direct-formats` - Get only direct audio formats (excluding HLS playlists)
- `GET /albums/{album_id}` - Get album details by ID
- `GET /playlists/{playlist_id}` - Get playlist details by ID
- `GET /artists/{artist_id}` - Get artist details by ID
- `GET /artists/{artist_id}/songs` - Get artist's top songs
- `GET /artists/{artist_id}/albums` - Get artist's albums
- `GET /artists/{artist_id}/playlists` - Get artist's playlists

## Configuration

The API uses environment variables for configuration. Create a `.env` file for local development:

```env
API_PREFIX=
```

## Health Check

The API includes a health check endpoint at `/health` that returns:

```json
{
  "status": "healthy"
}
```

This endpoint is useful for load balancers and monitoring systems. 