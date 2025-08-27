import asyncio
import yt_dlp
from typing import Optional, Dict, Any, List
import time
import random
import hashlib
from async_lru import alru_cache
import os
import json

class StreamService:
    def __init__(self):
        """Initialize the stream service."""
        self.cookie_file = os.getenv('YOUTUBE_COOKIE_FILE', 'cookies.txt')
        
        # Base yt-dlp options for reliable extraction
        self.base_ydl_opts = {
            'format': 'bestaudio[ext=mp4]/bestaudio[ext=webm]/bestaudio/best',
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            'extractor_retries': 3,
            'retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
            'keepvideo': False,
            'socket_timeout': 20,
            'extractor_timeout': 30,
            'sleep_interval': 1,
            'max_sleep_interval': 3,
            'no_color': True,
            'geo_bypass': True,
            'geo_bypass_country': 'IN',
        }

        # Optimized yt-dlp options for speed
        self.fast_ydl_opts = self.base_ydl_opts.copy()
        self.fast_ydl_opts.update({
            'extract_flat': True,
            'skip_download': True,
            'process': False,
            'extractor_timeout': 15,
            'socket_timeout': 10,
        })

    @alru_cache(maxsize=256)
    async def get_stream_url(self, video_id: str) -> Optional[str]:
        """
        Get the direct stream URL for a YouTube video ID with LRU caching.
        Tries a fast method first, then falls back to a more reliable one.
        """
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        loop = asyncio.get_event_loop()

        try:
            # First, try the faster extraction method
            result = await loop.run_in_executor(None, self._extract_info_from_url, video_url, True)
            if result:
                return result
        except Exception as e:
            print(f"Fast stream extraction failed for {video_id}: {e}. Falling back to standard method.")

        # If the fast method fails or returns nothing, fall back to the standard method
        try:
            result = await loop.run_in_executor(None, self._extract_info_from_url, video_url, False)
            return result
        except Exception as e:
            print(f"Standard stream extraction failed for {video_id}: {e}")
            return None

    def _get_ydl_opts(self, fast: bool) -> Dict[str, Any]:
        """Get yt-dlp options."""
        opts = self.fast_ydl_opts.copy() if fast else self.base_ydl_opts.copy()
        
        opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        if os.path.exists(self.cookie_file):
            with open(self.cookie_file, 'r') as f:
                content = f.read()
                if 'your_' not in content and 'value_here' not in content:
                    opts['cookiefile'] = self.cookie_file
                else:
                    print(f"Cookie file {self.cookie_file} contains placeholder values")
        return opts

    def _extract_info_from_url(self, url: str, fast: bool) -> Optional[str]:
        """
        Extracts stream URL from info dictionary.
        """
        opts = self._get_ydl_opts(fast)
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'url' in info and self._is_direct_audio_url(info['url']):
                return info['url']
            if 'formats' in info:
                for f in sorted(info['formats'], key=lambda x: x.get('abr', 0), reverse=True):
                    if self._is_valid_audio_format(f):
                        return f['url']
        return None

    def _is_direct_audio_url(self, url: str) -> bool:
        """
        Check if a URL is a direct audio URL (not HLS playlist).
        """
        return '.m3u8' not in url.lower() and 'manifest' not in url.lower()

    def _is_valid_audio_format(self, fmt: Dict[str, Any]) -> bool:
        """
        Check if a format is a valid audio format.
        """
        return fmt.get('acodec') != 'none' and fmt.get('url') and self._is_direct_audio_url(fmt.get('url', ''))

    async def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed video information including thumbnails.
        """
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._extract_video_info, video_url)
        except Exception as e:
            print(f"Error getting video info for {video_id}: {e}")
            return None

    def _extract_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract video information using yt-dlp.
        """
        try:
            with yt_dlp.YoutubeDL(self.base_ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'thumbnails': info.get('thumbnails', []),
                    'duration': info.get('duration'),
                    'title': info.get('title'),
                    'uploader': info.get('uploader'),
                }
        except Exception as e:
            print(f"Error extracting video info: {e}")
            return None
