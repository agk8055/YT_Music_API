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
        
        # Base yt-dlp options
        self.base_ydl_opts = {
            'format': 'bestaudio[ext=mp4]/bestaudio[ext=webm]/bestaudio/best',
            'extractaudio': False,
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
            'socket_timeout': 30,
            'extractor_timeout': 45,
            'sleep_interval': 1,
            'max_sleep_interval': 5,
            'no_color': True,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
        }

    @alru_cache(maxsize=128)
    async def get_stream_url(self, video_id: str) -> Optional[str]:
        """
        Get the direct stream URL for a YouTube video ID with LRU caching.
        """
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Run yt-dlp with increased timeout for Render
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._extract_stream_url, video_url),
                timeout=60.0
            )
            
            return result
        except asyncio.TimeoutError:
            print(f"Timeout getting stream URL for {video_id}")
            return None
        except Exception as e:
            print(f"Error getting stream URL for {video_id}: {e}")
            return None

    def _extract_stream_url(self, url: str) -> Optional[str]:
        """
        Extract stream URL with multiple strategies.
        """
        strategies = [
            self._extract_with_cookies,
            self._extract_without_cookies,
            self._extract_minimal_fallback
        ]
        
        for strategy in strategies:
            try:
                result = strategy(url)
                if result:
                    return result
            except Exception as e:
                print(f"Strategy {strategy.__name__} failed: {e}")
                continue
        
        return None

    def _get_ydl_opts(self, use_cookies: bool) -> Dict[str, Any]:
        """Get yt-dlp options with or without cookies."""
        opts = self.base_ydl_opts.copy()
        opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        if use_cookies and os.path.exists(self.cookie_file):
            with open(self.cookie_file, 'r') as f:
                content = f.read()
                if 'your_' not in content and 'value_here' not in content:
                    opts['cookiefile'] = self.cookie_file
                else:
                    print(f"Cookie file {self.cookie_file} contains placeholder values")
        return opts

    def _extract_with_cookies(self, url: str) -> Optional[str]:
        """Extract stream URL with cookie support."""
        opts = self._get_ydl_opts(use_cookies=True)
        if 'cookiefile' not in opts:
            return None
        return self._extract_info_from_url(url, opts)

    def _extract_without_cookies(self, url: str) -> Optional[str]:
        """Extract stream URL without cookies (fallback)."""
        opts = self._get_ydl_opts(use_cookies=False)
        opts['http_headers'].update({
            'Referer': 'https://www.youtube.com/',
            'Origin': 'https://www.youtube.com',
            'Sec-Fetch-Site': 'same-origin',
        })
        return self._extract_info_from_url(url, opts)

    def _extract_minimal_fallback(self, url: str) -> Optional[str]:
        """
        Minimal fallback method with basic configuration.
        """
        minimal_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 15,
            'extractor_timeout': 20,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
        }
        return self._extract_info_from_url(url, minimal_opts)

    def _extract_info_from_url(self, url: str, opts: Dict[str, Any]) -> Optional[str]:
        """
        Extracts stream URL from info dictionary.
        """
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