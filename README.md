# YT Music API

A FastAPI-based REST API that provides access to YouTube Music data and streaming capabilities.

## Features

- Global search across songs, albums, playlists, and artists
- Individual song, album, playlist, and artist endpoints
- Stream URL generation for songs
- Artist song listings

## Project Structure

```
YT_Music_API/
├── .gitignore             # To ignore Python cache, virtual envs, etc.
├── README.md              # Project documentation
├── requirements.txt       # Project dependencies
├── main.py                # Main FastAPI app entry point and router setup
├── config.py              # Application configuration (e.g., API prefixes)
│
├── api/                   # Directory for API endpoint routers
│   ├── __init__.py
│   ├── search.py          # Handles the global /search endpoint
│   ├── songs.py           # Handles the /song/{id} endpoint
│   ├── albums.py          # Handles the /album/{id} endpoint
│   ├── playlists.py       # Handles the /playlist/{id} endpoint
│   └── artists.py         # Handles /artist/{id} and /artist/{id}/songs
│
├── schemas/               # Pydantic models for data validation and response shapes
│   ├── __init__.py
│   ├── search.py          # Models for the global search response
│   ├── song.py            # Model for a single song
│   ├── album.py           # Model for an album
│   ├── playlist.py        # Model for a playlist
│   ├── artist.py          # Model for an artist
│   └── common.py          # Shared/common models (e.g., Thumbnail)
│
└── services/              # Business logic and external service integrations
    ├── __init__.py
    ├── ytm_service.py     # Logic for interacting with the ytmusicapi library
    └── stream_service.py  # Logic for getting stream URLs with yt-dlp
```

## Installation

1. Clone the repository
2. Install dependencies:

   **Option 1: Full installation (includes yt-dlp for streaming)**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Option 2: Basic installation (without yt-dlp - streaming will be disabled)**
   ```bash
   pip install -r requirements-simple.txt
   ```
   
   **Note:** If you encounter Rust compilation errors during installation, use Option 2 and install yt-dlp separately later if needed.

## Usage

1. **Test your setup first:**
   ```bash
   python test_setup.py
   ```

2. Start the server:
   ```bash
   python main.py
   ```

3. Access the API at `http://localhost:8000`

## Troubleshooting

### "Site does not support https" Error

This is a common issue with ytmusicapi. The updated service will:

1. **Use mock data for development** - The API will work even if YouTube Music is unavailable
2. **Provide better error handling** - Clear error messages and graceful fallbacks
3. **Test connection on startup** - Automatic detection of connection issues

### Connection Issues

If you're having trouble connecting to YouTube Music:

1. **Check your internet connection**
2. **Try updating ytmusicapi:**
   ```bash
   pip install --upgrade ytmusicapi
   ```
3. **Use the test script to diagnose:**
   ```bash
   python test_setup.py
   ```
4. **The app will work with mock data** for development and testing

## API Endpoints

- `GET /search` - Global search across all content types
- `GET /song/{id}` - Get song details
- `GET /album/{id}` - Get album details
- `GET /playlist/{id}` - Get playlist details
- `GET /artist/{id}` - Get artist details
- `GET /artist/{id}/songs` - Get artist's songs

## Development

This project uses:
- FastAPI for the web framework
- Pydantic for data validation
- ytmusicapi for YouTube Music integration
- yt-dlp for stream URL generation 