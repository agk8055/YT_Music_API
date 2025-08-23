import asyncio
import yt_dlp
from typing import Optional, Dict, Any, List
import time
import random
import hashlib
from functools import lru_cache

class StreamService:
    def __init__(self):
        """Initialize the stream service."""
        # Cache for stream URLs to avoid repeated requests
        self._stream_cache = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
        
        # Optimized yt-dlp options for faster extraction
        self.ydl_opts = {
            'format': 'bestaudio[ext=mp4]/bestaudio[ext=webm]/bestaudio/best',
            'extractaudio': False,
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            # Optimized headers for better success rate
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            # Reduced retries for faster failure detection
            'extractor_retries': 2,
            'retries': 2,
            'fragment_retries': 2,
            'skip_unavailable_fragments': True,
            'keepvideo': False,
            # Add timeout to prevent hanging
            'socket_timeout': 10,
            'extractor_timeout': 15,
        }

    def _get_cache_key(self, video_id: str) -> str:
        """Generate cache key for video ID."""
        return hashlib.md5(video_id.encode()).hexdigest()

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        return time.time() - cache_entry.get('timestamp', 0) < self._cache_ttl

    def clear_cache(self):
        """Clear the stream URL cache."""
        self._stream_cache.clear()
        print("Stream cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        valid_entries = sum(1 for entry in self._stream_cache.values() 
                          if self._is_cache_valid(entry))
        expired_entries = len(self._stream_cache) - valid_entries
        
        return {
            'total_entries': len(self._stream_cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_hit_rate': f"{valid_entries}/{len(self._stream_cache)}" if self._stream_cache else "0/0"
        }

    async def get_stream_url(self, video_id: str) -> Optional[str]:
        """
        Get the direct stream URL for a YouTube video ID with caching.
        
        Args:
            video_id: The YouTube video ID
            
        Returns:
            Direct stream URL or None if failed
        """
        # Check cache first
        cache_key = self._get_cache_key(video_id)
        if cache_key in self._stream_cache:
            cache_entry = self._stream_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                print(f"Cache hit for {video_id}")
                return cache_entry['url']
            else:
                # Remove expired cache entry
                del self._stream_cache[cache_key]

        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Reduced delay for faster response
            await asyncio.sleep(random.uniform(0.05, 0.2))
            
            # Run yt-dlp with timeout
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._extract_stream_url_optimized, video_url),
                timeout=20.0  # 20 second timeout
            )
            
            # Cache successful result
            if result:
                self._stream_cache[cache_key] = {
                    'url': result,
                    'timestamp': time.time()
                }
            
            return result
        except asyncio.TimeoutError:
            print(f"Timeout getting stream URL for {video_id}")
            return None
        except Exception as e:
            print(f"Error getting stream URL for {video_id}: {e}")
            return None

    def _extract_stream_url_optimized(self, url: str) -> Optional[str]:
        """
        Optimized stream URL extraction with single strategy and better error handling.
        
        Args:
            url: The YouTube URL
            
        Returns:
            Direct stream URL or None if failed
        """
        try:
            # Use a single, optimized strategy
            opts = self.ydl_opts.copy()
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Try to get direct URL first
                if 'url' in info:
                    url_value = info['url']
                    if self._is_direct_audio_url(url_value):
                        return url_value
                
                # If no direct URL, find best audio format
                if 'formats' in info:
                    formats = info['formats']
                    audio_formats = [f for f in formats if self._is_valid_audio_format(f)]
                    
                    if audio_formats:
                        # Sort by quality and prefer certain formats
                        audio_formats.sort(key=lambda x: (
                            x.get('abr', 0) or 0,  # Audio bitrate
                            x.get('filesize', 0) or 0,  # File size
                            # Prefer mp4a codec and mp4/m4a extensions
                            1 if x.get('acodec', '').startswith('mp4a') else 0,
                            1 if x.get('ext') in ['m4a', 'mp4'] else 0,
                            1 if x.get('ext') == 'webm' else 0
                        ), reverse=True)
                        
                        return audio_formats[0]['url']
                
                return None
                
        except Exception as e:
            print(f"Error in optimized stream URL extraction: {e}")
            # Try fallback with minimal options
            return self._extract_stream_url_fallback_minimal(url)

    def _extract_stream_url_fallback_minimal(self, url: str) -> Optional[str]:
        """
        Minimal fallback method with basic configuration.
        
        Args:
            url: The YouTube URL
            
        Returns:
            Direct stream URL or None if failed
        """
        try:
            minimal_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'extractaudio': False,
                'noplaylist': True,
                'socket_timeout': 5,
                'extractor_timeout': 10,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                },
            }
            
            with yt_dlp.YoutubeDL(minimal_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'url' in info:
                    return info['url']
                
                elif 'formats' in info:
                    formats = info['formats']
                    for fmt in formats:
                        if self._is_valid_audio_format(fmt):
                            return fmt['url']
                
                return None
        except Exception as e:
            print(f"Error in minimal fallback: {e}")
            return None

    def _is_direct_audio_url(self, url: str) -> bool:
        """
        Check if a URL is a direct audio URL (not HLS playlist).
        
        Args:
            url: The URL to check
            
        Returns:
            True if it's a direct audio URL, False otherwise
        """
        # Check for HLS playlist indicators
        hls_indicators = ['.m3u8', 'manifest', 'playlist', 'hls']
        url_lower = url.lower()
        
        for indicator in hls_indicators:
            if indicator in url_lower:
                return False
        
        # Check for direct audio file extensions
        audio_extensions = ['.mp4', '.webm', '.m4a', '.mp3', '.aac', '.ogg']
        for ext in audio_extensions:
            if ext in url_lower:
                return True
        
        # If no clear indicators, assume it's direct if it doesn't contain HLS indicators
        return True

    def _is_valid_audio_format(self, fmt: Dict[str, Any]) -> bool:
        """
        Check if a format is a valid audio format.
        
        Args:
            fmt: The format dictionary
            
        Returns:
            True if it's a valid audio format, False otherwise
        """
        # Must have audio codec
        if fmt.get('acodec') == 'none':
            return False
        
        # Must have a URL
        if not fmt.get('url'):
            return False
        
        # Check if URL is not an HLS playlist
        url = fmt.get('url', '').lower()
        hls_indicators = ['.m3u8', 'manifest', 'playlist', 'hls']
        
        for indicator in hls_indicators:
            if indicator in url:
                return False
        
        # Accept any format with audio codec, but prefer specific extensions
        ext = fmt.get('ext', '').lower()
        preferred_extensions = ['mp4', 'webm', 'm4a', 'mp3', 'aac']
        
        # If it has a preferred extension, accept it
        if ext in preferred_extensions:
            return True
        
        # If it has any audio codec and no HLS indicators, accept it
        return fmt.get('acodec') != 'none'

    def _extract_stream_url_fallback(self, url: str) -> Optional[str]:
        """
        Fallback method with more basic yt-dlp configuration.
        
        Args:
            url: The YouTube URL
            
        Returns:
            Direct stream URL or None if failed
        """
        try:
            fallback_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'extractaudio': False,
                'noplaylist': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                },
            }
            
            with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'url' in info:
                    url_value = info['url']
                    if self._is_direct_audio_url(url_value):
                        return url_value
                
                elif 'formats' in info:
                    formats = info['formats']
                    # Get any format with audio that's not HLS
                    for fmt in formats:
                        if self._is_valid_audio_format(fmt):
                            return fmt['url']
                
                return None
        except Exception as e:
            print(f"Error in fallback stream URL extraction: {e}")
            return None

    async def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed video information including thumbnails.
        
        Args:
            video_id: The YouTube video ID
            
        Returns:
            Video info dictionary or None if failed
        """
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Run yt-dlp in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._extract_video_info, video_url)
            return result
        except Exception as e:
            print(f"Error getting video info for {video_id}: {e}")
            return None

    async def get_available_formats(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get all available audio formats for a video.
        
        Args:
            video_id: The YouTube video ID
            
        Returns:
            List of available audio formats or None if failed
        """
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Run yt-dlp in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._extract_available_formats, video_url)
            return result
        except Exception as e:
            print(f"Error getting available formats for {video_id}: {e}")
            return None

    async def get_direct_audio_formats(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get only direct audio formats (excluding HLS playlists).
        
        Args:
            video_id: The YouTube video ID
            
        Returns:
            List of direct audio formats or None if failed
        """
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Run yt-dlp in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._extract_direct_audio_formats, video_url)
            return result
        except Exception as e:
            print(f"Error getting direct audio formats for {video_id}: {e}")
            return None

    async def test_video_accessibility(self, video_id: str) -> Dict[str, Any]:
        """
        Test if a video is accessible and get basic info.
        
        Args:
            video_id: The YouTube video ID
            
        Returns:
            Dictionary with accessibility status and info
        """
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            test_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                },
            }
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._test_video_access, video_url, test_opts)
            return result
        except Exception as e:
            return {
                "accessible": False,
                "error": str(e),
                "video_id": video_id
            }

    def _extract_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract video information using yt-dlp.
        
        Args:
            url: The YouTube URL
            
        Returns:
            Video info dictionary or None if failed
        """
        try:
            info_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'no_warnings': True,
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(info_opts) as ydl:
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

    def _extract_available_formats(self, url: str) -> Optional[List[Dict[str, Any]]]:
        """
        Extract all available audio formats for a video.
        
        Args:
            url: The YouTube URL
            
        Returns:
            List of available audio formats or None if failed
        """
        try:
            info_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'no_warnings': True,
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'formats' in info:
                    formats = info['formats']
                    audio_formats = []
                    
                    for fmt in formats:
                        if self._is_valid_audio_format(fmt):
                            audio_formats.append({
                                'format_id': fmt.get('format_id'),
                                'ext': fmt.get('ext'),
                                'abr': fmt.get('abr'),  # Audio bitrate
                                'filesize': fmt.get('filesize'),
                                'height': fmt.get('height'),
                                'width': fmt.get('width'),
                                'acodec': fmt.get('acodec'),
                                'vcodec': fmt.get('vcodec'),
                                'url': fmt.get('url'),
                                'is_direct': self._is_direct_audio_url(fmt.get('url', '')),
                                'url_preview': fmt.get('url', '')[:100] + '...' if fmt.get('url') else None
                            })
                    
                    # Sort by quality (bitrate, filesize)
                    audio_formats.sort(key=lambda x: (
                        x.get('abr', 0) or 0,
                        x.get('filesize', 0) or 0
                    ), reverse=True)
                    
                    return audio_formats
                
                return []
        except Exception as e:
            print(f"Error extracting available formats: {e}")
            return None

    def _extract_direct_audio_formats(self, url: str) -> Optional[List[Dict[str, Any]]]:
        """
        Extract only direct audio formats (excluding HLS playlists).
        
        Args:
            url: The YouTube URL
            
        Returns:
            List of direct audio formats or None if failed
        """
        try:
            info_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'formats' in info:
                    formats = info['formats']
                    direct_audio_formats = []
                    
                    for fmt in formats:
                        if self._is_valid_audio_format(fmt) and self._is_direct_audio_url(fmt.get('url', '')):
                            direct_audio_formats.append({
                                'format_id': fmt.get('format_id'),
                                'ext': fmt.get('ext'),
                                'abr': fmt.get('abr'),  # Audio bitrate
                                'filesize': fmt.get('filesize'),
                                'height': fmt.get('height'),
                                'width': fmt.get('width'),
                                'acodec': fmt.get('acodec'),
                                'vcodec': fmt.get('vcodec'),
                                'url': fmt.get('url'),
                                'url_preview': fmt.get('url', '')[:100] + '...' if fmt.get('url') else None
                            })
                    
                    # Sort by quality (bitrate, filesize)
                    direct_audio_formats.sort(key=lambda x: (
                        x.get('abr', 0) or 0,
                        x.get('filesize', 0) or 0
                    ), reverse=True)
                    
                    return direct_audio_formats
                
                return []
        except Exception as e:
            print(f"Error extracting direct audio formats: {e}")
            return None

    def _test_video_access(self, url: str, opts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test if a video is accessible with given options.
        
        Args:
            url: The YouTube URL
            opts: yt-dlp options
            
        Returns:
            Dictionary with accessibility status and info
        """
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    "accessible": True,
                    "title": info.get('title'),
                    "duration": info.get('duration'),
                    "uploader": info.get('uploader'),
                    "view_count": info.get('view_count'),
                    "like_count": info.get('like_count'),
                    "availability": info.get('availability'),
                    "age_limit": info.get('age_limit'),
                }
        except Exception as e:
            return {
                "accessible": False,
                "error": str(e),
                "error_type": type(e).__name__
            } 