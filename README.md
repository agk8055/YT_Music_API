# YouTube Music API

A FastAPI-based REST API for YouTube Music data and streaming, optimized for deployment on Render.

## Features

- 🔍 Search for songs, albums, playlists, and artists
- 🎵 Get song details and stream URLs
- 📱 RESTful API with comprehensive documentation
- ⚡ Optimized for performance with caching
- 🔒 Cookie-based authentication to bypass bot detection
- 🚀 Ready for deployment on Render

## Quick Start

### Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd YT_Music_API
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up YouTube cookies (recommended for better access):
   - Install a browser extension like "Get cookies.txt" or "Cookie Quick Manager"
   - Go to https://www.youtube.com and sign in
   - Export cookies for youtube.com domain
   - Save them to `cookies.txt` in the project root

4. Run the development server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Deployment on Render

1. **Fork/Clone this repository** to your GitHub account

2. **Set up YouTube Cookies** (Highly Recommended):
   - Install a browser extension like "Get cookies.txt" or "Cookie Quick Manager"
   - Go to https://www.youtube.com and sign in
   - Export cookies for youtube.com domain
   - Create a `cookies.txt` file in your repository root with the exported cookies
   - The format should be:
     ```
     .youtube.com	TRUE	/	FALSE	1735689600	VISITOR_INFO1_LIVE	your_cookie_value_here
     .youtube.com	TRUE	/	FALSE	1735689600	LOGIN_INFO	your_cookie_value_here
     .youtube.com	TRUE	/	FALSE	1735689600	SID	your_cookie_value_here
     # ... more cookies
     ```

3. **Deploy to Render**:
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: `yt-music-api` (or your preferred name)
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn main:app -c gunicorn.conf.py`
     - **Plan**: Free (or paid for better performance)

4. **Environment Variables** (Optional):
   - `YOUTUBE_COOKIE_FILE`: Path to cookie file (default: `cookies.txt`)

## API Endpoints

### Search
- `GET /api/search?q={query}&limit={limit}` - Search for songs, albums, playlists, artists
- `GET /api/search/songs?q={query}&limit={limit}` - Search for songs only
- `GET /api/search/albums?q={query}&limit={limit}` - Search for albums only
- `GET /api/search/artists?q={query}&limit={limit}` - Search for artists only
- `GET /api/search/playlists?q={query}&limit={limit}` - Search for playlists only
- `GET /api/search/suggestions?q={query}&limit={limit}` - Get search suggestions

### Songs
- `GET /api/song/{song_id}` - Get song details
- `GET /api/song/{song_id}/stream` - Get stream URL
- `GET /api/song/{song_id}/formats` - Get available audio formats
- `GET /api/song/{song_id}/direct-formats` - Get direct audio formats only
- `GET /api/song/{song_id}/test` - Test video accessibility

### Streaming
- `GET /proxy-stream/{song_id}` - Proxy stream audio directly to client with seeking support
- `HEAD /proxy-stream/{song_id}` - Get stream metadata without downloading audio
- `OPTIONS /proxy-stream/{song_id}` - CORS preflight support

### Albums
- `GET /api/album/{album_id}` - Get album details with tracks

### Playlists
- `GET /api/playlist/{playlist_id}` - Get playlist details with tracks

### Artists
- `GET /api/artist/{artist_id}` - Get artist details
- `GET /api/artist/{artist_id}/songs` - Get artist's top songs
- `GET /api/artist/{artist_id}/albums` - Get artist's albums
- `GET /api/artist/{artist_id}/playlists` - Get artist's playlists

### Top Songs
- `GET /api/top-songs?region={region}&limit={limit}` - Get top songs globally or by region

## Troubleshooting

### Common Issues on Render

1. **"Sign in to confirm you're not a bot" Error**:
   - This is YouTube's bot detection system
   - **Solution**: Add YouTube cookies to bypass this
   - Follow the cookie setup instructions above

2. **Timeout Errors**:
   - The API has been optimized with longer timeouts for Render
   - If you still get timeouts, try:
     - Using the `/test` endpoint to check video accessibility
     - Adding cookies for better access
     - Trying a different video ID

3. **Stream URL Returns Null**:
   - This can happen due to region restrictions or video availability
   - **Solutions**:
     - Add YouTube cookies
     - Check if the video is publicly accessible
     - Try the `/formats` endpoint to see available formats

### Cookie Setup Guide

1. **Chrome Extension Method**:
   - Install "Get cookies.txt" extension
   - Go to https://www.youtube.com and sign in
   - Click the extension icon → Export → Select youtube.com
   - Save as `cookies.txt` in your project root

2. **Firefox Extension Method**:
   - Install "Cookie Quick Manager" extension
   - Go to https://www.youtube.com and sign in
   - Open the extension → Export → Select youtube.com
   - Save as `cookies.txt` in your project root

3. **Manual Method**:
   - Open browser dev tools → Application/Storage → Cookies
   - Find youtube.com cookies
   - Copy the important ones (SID, HSID, SSID, etc.)
   - Format them according to the template in `cookies.txt`

### Performance Tips

1. **Use Caching**: The API caches stream URLs for 1 hour
2. **Batch Requests**: Make multiple requests in parallel when possible
3. **Error Handling**: Use the `/test` endpoint to check video accessibility before requesting streams
4. **Rate Limiting**: The API includes rate limiting to avoid being blocked by YouTube

### Proxy Streaming

The `/proxy-stream/{song_id}` endpoint provides direct audio streaming with several advantages:

- **Direct Streaming**: Audio streams directly to the client without exposing YouTube URLs
- **Seeking Support**: Supports HTTP Range requests for audio seeking in media players
- **Format Control**: Accepts format and quality parameters for optimal streaming
- **Error Handling**: Comprehensive error handling with meaningful error messages

**Usage Examples**:
```bash
# Basic streaming
GET /proxy-stream/dQw4w9WgXcQ

# With format preference
GET /proxy-stream/dQw4w9WgXcQ?format=bestaudio&quality=128

# With range request for seeking
GET /proxy-stream/dQw4w9WgXcQ
Range: bytes=0-1048575

# Get metadata only (HEAD request)
HEAD /proxy-stream/dQw4w9WgXcQ

# CORS preflight (OPTIONS request)
OPTIONS /proxy-stream/dQw4w9WgXcQ
```

**Query Parameters**:
- `format`: Audio format preference (default: "bestaudio")
- `quality`: Quality preference (default: "best")
- `range`: HTTP Range header for seeking support

## Development

### Project Structure
```
YT_Music_API/
├── api/                    # API endpoints
├── schemas/               # Pydantic models
├── services/              # Business logic
├── main.py               # FastAPI app
├── requirements.txt      # Dependencies
├── gunicorn.conf.py     # Production server config
├── cookies.txt          # YouTube cookies (create this)
└── README.md           # This file
```

### Adding New Features

1. **New Endpoint**: Add to appropriate file in `api/`
2. **New Schema**: Create in `schemas/`
3. **New Service**: Add to `services/`
4. **Update Dependencies**: Add to `requirements.txt`

### Testing

Test the API endpoints using the interactive documentation at `http://localhost:8000/docs` or `https://your-render-app.onrender.com/docs`

## License

This project is for educational purposes. Please respect YouTube's terms of service and use responsibly.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the error messages in your Render logs
3. Try the `/test` endpoint to diagnose video accessibility
4. Ensure you have proper cookies set up 