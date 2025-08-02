# Top Songs API Endpoints

This document describes the new top songs API endpoints that provide access to trending and popular songs globally and by country.

## Endpoints

### 1. Get Top Songs (Global or Country-Specific)

**Endpoint:** `GET /top-songs`

**Description:** Get top latest songs globally or for a specific country/region.

**Parameters:**
- `region` (optional): Country/region code (e.g., 'US', 'IN', 'GB'). If not provided, returns global top songs
- `limit` (optional): Maximum number of songs to return (1-50, default: 20)

**Example Requests:**
```bash
# Get global top songs (default)
curl -X GET "http://localhost:8000/top-songs?limit=10"

# Get top songs for a specific country
curl -X GET "http://localhost:8000/top-songs?region=US&limit=15"
```

**Response:**
```json
{
  "songs": [
    {
      "id": "J7p4bzqLvCw",
      "title": "Blinding Lights",
      "artist": "The Weeknd",
      "album": "Blinding Lights",
      "duration": "3:22",
      "thumbnails": [...],
      "url": "https://www.youtube.com/watch?v=J7p4bzqLvCw",
      "stream_url": null
    }
  ],
  "region": "US",
  "total_count": 15,
  "message": "Top 15 songs for US"
}
```

### 2. Get Global Top Songs

**Endpoint:** `GET /top-songs/global`

**Description:** Get global top latest songs.

**Parameters:**
- `limit` (optional): Maximum number of songs to return (1-50, default: 20)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/top-songs/global?limit=10"
```

### 3. Get Country-Specific Top Songs

**Endpoint:** `GET /top-songs/country/{country_code}`

**Description:** Get top latest songs for a specific country.

**Parameters:**
- `country_code` (path): Country code (e.g., 'US', 'IN', 'GB', 'CA', 'AU')
- `limit` (optional): Maximum number of songs to return (1-50, default: 20)

**Example Requests:**
```bash
# Get top songs for United States
curl -X GET "http://localhost:8000/top-songs/country/US?limit=10"

# Get top songs for India
curl -X GET "http://localhost:8000/top-songs/country/IN?limit=10"

# Get top songs for United Kingdom
curl -X GET "http://localhost:8000/top-songs/country/GB?limit=10"
```

## Supported Country Codes

The API supports standard ISO 3166-1 alpha-2 country codes. Some popular examples:

- `US` - United States
- `IN` - India
- `GB` - United Kingdom
- `CA` - Canada
- `AU` - Australia
- `DE` - Germany
- `FR` - France
- `JP` - Japan
- `BR` - Brazil
- `MX` - Mexico

## Response Schema

All endpoints return a `TopSongsResponse` object with the following structure:

```json
{
  "songs": [
    {
      "id": "string",
      "title": "string",
      "artist": "string",
      "album": "string",
      "duration": "string",
      "thumbnails": [
        {
          "url": "string",
          "width": "integer",
          "height": "integer"
        }
      ],
      "url": "string",
      "stream_url": "string"
    }
  ],
  "region": "string",
  "total_count": "integer",
  "message": "string"
}
```

## Features

- **Smart Search**: Uses multiple search strategies to find trending songs
- **Deduplication**: Ensures no duplicate songs in the results
- **Flexible Limits**: Request 1-50 songs per call
- **Country Support**: Get region-specific trending songs
- **Global Coverage**: Access worldwide trending music
- **Rich Metadata**: Includes thumbnails, duration, and YouTube URLs

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Successful request
- `500 Internal Server Error`: Server-side error

## Rate Limiting

Currently, there are no rate limits implemented, but it's recommended to make reasonable requests to avoid overwhelming the YouTube Music API.

## Notes

- Results are based on YouTube Music search algorithms and may vary over time
- Song availability depends on YouTube Music's catalog in each region
- The API uses multiple search strategies to ensure diverse and relevant results 