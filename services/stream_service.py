import asyncio
import yt_dlp
from typing import Optional, Dict, Any, List

class StreamService:
    def __init__(self):
        """Initialize the stream service."""
        self.ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
            'extractaudio': True,
            'audioformat': 'best',
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
            'no_warnings': True,
            'quiet': True,
        }

    async def get_stream_url(self, video_id: str) -> Optional[str]:
        """
        Get the direct stream URL for a YouTube video ID.
        
        Args:
            video_id: The YouTube video ID
            
        Returns:
            Direct stream URL or None if failed
        """
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Run yt-dlp in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._extract_stream_url, video_url)
            return result
        except Exception as e:
            print(f"Error getting stream URL for {video_id}: {e}")
            return None

    def _extract_stream_url(self, url: str) -> Optional[str]:
        """
        Extract the direct stream URL using yt-dlp.
        
        Args:
            url: The YouTube URL
            
        Returns:
            Direct stream URL or None if failed
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Get the best audio format URL
                if 'url' in info:
                    return info['url']
                elif 'formats' in info:
                    # Find the best audio format
                    formats = info['formats']
                    audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('url')]
                    
                    if audio_formats:
                        # Sort by audio quality: bitrate, filesize, and prefer certain formats
                        audio_formats.sort(key=lambda x: (
                            x.get('abr', 0) or 0,  # Audio bitrate (highest priority)
                            x.get('filesize', 0) or 0,  # File size (higher = better quality)
                            x.get('height', 0) or 0,  # Height as fallback
                            # Prefer certain audio codecs
                            1 if x.get('acodec', '').startswith('mp4a') else 0,
                            1 if x.get('ext') in ['m4a', 'webm'] else 0
                        ), reverse=True)
                        
                        # Select the best format
                        best_format = audio_formats[0]
                        
                        return best_format['url']
                
                return None
        except Exception as e:
            print(f"Error extracting stream URL: {e}")
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
                        if fmt.get('acodec') != 'none' and fmt.get('url'):
                            audio_formats.append({
                                'format_id': fmt.get('format_id'),
                                'ext': fmt.get('ext'),
                                'abr': fmt.get('abr'),  # Audio bitrate
                                'filesize': fmt.get('filesize'),
                                'height': fmt.get('height'),
                                'width': fmt.get('width'),
                                'acodec': fmt.get('acodec'),
                                'vcodec': fmt.get('vcodec'),
                                'url': fmt.get('url')
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