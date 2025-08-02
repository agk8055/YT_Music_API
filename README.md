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

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /docs` - API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

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