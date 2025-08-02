import asyncio
from typing import List, Dict, Any
from ytmusicapi import YTMusic
from .stream_service import StreamService

class YTMService:
    def __init__(self):
        """
        Initializes the YTMusic service.
        This will raise an exception if YTMusic cannot be initialized.
        """
        try:
            self.ytm = YTMusic()
            self.stream_service = StreamService()
            print("✅ YTMusic initialized successfully")
        except Exception as e:
            print(f"❌ YTMusic initialization failed: {e}")
            raise e

    def _parse_track_count(self, track_count) -> str:
        """
        Parse and validate track count from various formats.
        Returns a validated track count string or None if invalid.
        """
        if track_count is None:
            return None
            
        # If it's already an integer, convert to string
        if isinstance(track_count, int):
            return str(track_count)
            
        # If it's a string, try to parse it
        if isinstance(track_count, str):
            track_count = track_count.strip()
            
            # Handle common formats like "1.3M", "3.8K", "1.2B"
            if track_count.endswith('K'):
                try:
                    number = float(track_count[:-1])
                    total = int(number * 1000)
                    # Validate: reasonable limit for a playlist
                    if total <= 10000:  # Max 10K tracks
                        return str(total)
                    else:
                        print(f"Warning: Suspicious track count '{track_count}' converted to {total}, capping at 10000")
                        return "10000"
                except ValueError:
                    return None
                    
            elif track_count.endswith('M'):
                try:
                    number = float(track_count[:-1])
                    total = int(number * 1000000)
                    # This is definitely too high for a playlist
                    print(f"Warning: Unrealistic track count '{track_count}' ({total} tracks), capping at 10000")
                    return "10000"
                except ValueError:
                    return None
                    
            elif track_count.endswith('B'):
                try:
                    number = float(track_count[:-1])
                    total = int(number * 1000000000)
                    # This is definitely too high for a playlist
                    print(f"Warning: Unrealistic track count '{track_count}' ({total} tracks), capping at 10000")
                    return "10000"
                except ValueError:
                    return None
                    
            else:
                # Try to parse as a regular number
                try:
                    number = int(track_count)
                    # Validate: reasonable limit for a playlist
                    if number <= 10000:  # Max 10K tracks
                        return str(number)
                    else:
                        print(f"Warning: High track count '{track_count}', capping at 10000")
                        return "10000"
                except ValueError:
                    return None
        
        return None

    async def _execute_async(self, func, *args, **kwargs):
        """
        Asynchronously executes a ytmusicapi function.
        """
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        except Exception as e:
            print(f"❌ YTMusic API error in {getattr(func, '__name__', 'unknown_function')}: {e}")
            raise e

    async def search(self, query: str, limit: int = 20, include_stream_urls: bool = False) -> List[Dict[str, Any]]:
        """
        Search for songs, albums, playlists, and artists.
        """
        results = await self._execute_async(self.ytm.search, query, limit=limit)
        transformed_results = self._transform_search_results(results)
        
        # Add stream URLs if requested
        if include_stream_urls:
            await self._add_stream_urls(transformed_results)
        
        return transformed_results

    async def search_songs(self, query: str, limit: int = 20, include_stream_urls: bool = False) -> List[Dict[str, Any]]:
        """
        Search for songs only.
        """
        results = await self._execute_async(self.ytm.search, query, limit=limit, filter="songs")
        transformed_results = self._transform_search_results(results)
        
        # Add stream URLs if requested
        if include_stream_urls:
            await self._add_stream_urls(transformed_results)
        
        return transformed_results

    async def search_albums(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for albums only.
        """
        results = await self._execute_async(self.ytm.search, query, limit=limit, filter="albums")
        transformed_results = self._transform_search_results(results)
        return transformed_results

    async def search_artists(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for artists only.
        """
        results = await self._execute_async(self.ytm.search, query, limit=limit, filter="artists")
        transformed_results = self._transform_search_results(results)
        return transformed_results

    async def search_playlists(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for playlists only.
        """
        results = await self._execute_async(self.ytm.search, query, limit=limit, filter="playlists")
        transformed_results = self._transform_search_results(results)
        return transformed_results

    async def get_search_suggestion(self, query: str, limit: int = 10) -> List[str]:
        """
        Get search suggestions/autocomplete for a given query.
        """
        try:
            # Use the search function with a small limit to get suggestions
            # We'll extract titles from the results to use as suggestions
            results = await self._execute_async(self.ytm.search, query, limit=limit * 2)
            
            suggestions = []
            seen_suggestions = set()
            
            for item in results:
                if len(suggestions) >= limit:
                    break
                    
                # Extract suggestion from different result types
                suggestion = None
                if item.get('resultType') == 'song':
                    title = item.get('title', '')
                    artist = item.get('artists', [])
                    if artist and isinstance(artist, list) and len(artist) > 0:
                        artist_name = artist[0].get('name', '') if isinstance(artist[0], dict) else str(artist[0])
                        suggestion = f"{title} - {artist_name}"
                    else:
                        suggestion = title
                elif item.get('resultType') == 'album':
                    title = item.get('title', '')
                    artist = item.get('artists', [])
                    if artist and isinstance(artist, list) and len(artist) > 0:
                        artist_name = artist[0].get('name', '') if isinstance(artist[0], dict) else str(artist[0])
                        suggestion = f"{title} - {artist_name}"
                    else:
                        suggestion = title
                elif item.get('resultType') == 'artist':
                    # For artist results, try multiple possible field names for artist name
                    artist_name = None
                    
                    # Try different possible field names for artist name
                    possible_name_fields = ['artist', 'name', 'title', 'author']
                    for field in possible_name_fields:
                        artist_name = item.get(field)
                        if artist_name:
                            break
                    
                    # If still no name found, try to extract from artists array
                    if not artist_name and item.get('artists'):
                        artists = item.get('artists', [])
                        if isinstance(artists, list) and artists:
                            artist_name = artists[0].get('name') if isinstance(artists[0], dict) else str(artists[0])
                    
                    # Ensure artist name is not None
                    if artist_name is None:
                        artist_name = "Unknown Artist"
                    
                    suggestion = artist_name
                elif item.get('resultType') == 'playlist':
                    suggestion = item.get('title', '')
                
                # Add suggestion if it's valid and not already seen
                if suggestion and suggestion.strip() and suggestion not in seen_suggestions:
                    suggestions.append(suggestion.strip())
                    seen_suggestions.add(suggestion.strip())
            
            return suggestions
            
        except Exception as e:
            print(f"Error getting search suggestions for '{query}': {e}")
            return []

    async def get_song(self, song_id: str) -> Dict[str, Any]:
        """
        Get song details by ID.
        """
        song_data = await self._execute_async(self.ytm.get_song, song_id)
        return self._transform_song_data(song_data)

    async def get_album(self, album_id: str) -> Dict[str, Any]:
        """
        Get album details by ID.
        """
        album_data = await self._execute_async(self.ytm.get_album, album_id)
        return self._transform_album_data(album_data)

    async def get_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """
        Get playlist details by ID.
        """
        playlist_data = await self._execute_async(self.ytm.get_playlist, playlist_id)
        return self._transform_playlist_data(playlist_data)

    async def get_artist(self, artist_id: str) -> Dict[str, Any]:
        """
        Get artist details by ID.
        """
        artist_data = await self._execute_async(self.ytm.get_artist, artist_id)
        return self._transform_artist_data(artist_data)

    async def get_artist_songs(self, artist_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get artist's top songs by artist ID.
        """
        try:
            # Get artist data first to get the artist name
            artist_data = await self._execute_async(self.ytm.get_artist, artist_id)
            artist_name = artist_data.get('name', 'Unknown Artist')
            
            # Search for songs by the artist name to get top songs
            search_query = f"{artist_name} songs"
            search_results = await self._execute_async(self.ytm.search, search_query, limit=limit * 2)  # Get more results to filter
            
            # Filter results to only include actual songs (not playlists/albums) by this specific artist
            filtered_songs = []
            for item in search_results:
                # Only include items that are actually songs
                if item.get('resultType') == 'song':
                    # Check if the song has artists and if the target artist is in the list
                    artists = item.get('artists', [])
                    if isinstance(artists, list):
                        for artist in artists:
                            if isinstance(artist, dict) and artist.get('name'):
                                if artist_name.lower() in artist.get('name', '').lower():
                                    filtered_songs.append(item)
                                    break
                    
                    # If we have enough songs, stop
                    if len(filtered_songs) >= limit:
                        break
            
            # If we don't have enough filtered results, try a different search approach
            if len(filtered_songs) < limit:
                # Try searching for specific popular songs by the artist
                popular_songs = [
                    "Why This Kolaveri Di",
                    "Selfie Pulla", 
                    "Arabic Kuthu",
                    "Vaathi Coming",
                    "Hukum",
                    "Kaavaalaa",
                    "Ordinary Person",
                    "Pathala Pathala",
                    "Bloody Sweet",
                    "Lokiverse"
                ]
                
                for song_name in popular_songs:
                    if len(filtered_songs) >= limit:
                        break
                        
                    search_query = f"{artist_name} {song_name}"
                    song_results = await self._execute_async(self.ytm.search, search_query, limit=5)
                    
                    for item in song_results:
                        if item.get('resultType') == 'song':
                            artists = item.get('artists', [])
                            if isinstance(artists, list):
                                for artist in artists:
                                    if isinstance(artist, dict) and artist.get('name'):
                                        if artist_name.lower() in artist.get('name', '').lower():
                                            # Check if this song is not already in the list
                                            song_id = item.get('videoId')
                                            if not any(s.get('videoId') == song_id for s in filtered_songs):
                                                filtered_songs.append(item)
                                                break
                                if len(filtered_songs) >= limit:
                                    break
            
            return self._transform_songs_data(filtered_songs)
            
        except Exception as e:
            print(f"Error getting artist songs for {artist_id}: {e}")
            # Return empty list if there's an error
            return []

    async def get_artist_playlists(self, artist_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get artist's top playlists by artist ID.
        """
        try:
            # Get artist data first to get the artist name
            artist_data = await self._execute_async(self.ytm.get_artist, artist_id)
            artist_name = artist_data.get('name', 'Unknown Artist')
            
            # Search for playlists by the artist name
            search_query = f"{artist_name} playlist"
            search_results = await self._execute_async(self.ytm.search, search_query, limit=limit * 2)
            
            # Filter results to only include playlists by this specific artist
            filtered_playlists = []
            for item in search_results:
                # Only include items that are actually playlists
                if item.get('resultType') == 'playlist':
                    # Check if the playlist has author and if the target artist is in the list
                    author = item.get('author')
                    if isinstance(author, list) and author:
                        author_name = author[0].get('name', '') if isinstance(author[0], dict) else str(author[0])
                    elif isinstance(author, str):
                        author_name = author
                    else:
                        author_name = ''
                    
                    # Check if artist name is in the author or title
                    if (artist_name.lower() in author_name.lower() or 
                        artist_name.lower() in item.get('title', '').lower()):
                        filtered_playlists.append(item)
                    
                    # If we have enough playlists, stop
                    if len(filtered_playlists) >= limit:
                        break
            
            # If we don't have enough filtered results, try a different search approach
            if len(filtered_playlists) < limit:
                # Try searching for specific popular playlists by the artist
                popular_playlist_terms = [
                    "best hits",
                    "top songs",
                    "greatest hits",
                    "popular songs",
                    "hit songs"
                ]
                
                for term in popular_playlist_terms:
                    if len(filtered_playlists) >= limit:
                        break
                        
                    search_query = f"{artist_name} {term}"
                    playlist_results = await self._execute_async(self.ytm.search, search_query, limit=5)
                    
                    for item in playlist_results:
                        if item.get('resultType') == 'playlist':
                            # Check if this playlist is not already in the list
                            playlist_id = item.get('playlistId') or item.get('browseId')
                            if not any(p.get('playlistId') == playlist_id or p.get('browseId') == playlist_id 
                                     for p in filtered_playlists):
                                filtered_playlists.append(item)
                                if len(filtered_playlists) >= limit:
                                    break
                    
                    if len(filtered_playlists) >= limit:
                        break
            
            return self._transform_playlists_data(filtered_playlists)
            
        except Exception as e:
            print(f"Error getting artist playlists for {artist_id}: {e}")
            # Return empty list if there's an error
            return []

    async def get_artist_albums(self, artist_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get artist's albums by artist ID, sorted by release date (latest first).
        """
        try:
            # Get artist data first to get the artist name
            artist_data = await self._execute_async(self.ytm.get_artist, artist_id)
            artist_name = artist_data.get('name', 'Unknown Artist')
            
            # Search for albums by the artist name - use more specific search terms
            search_queries = [
                f"{artist_name} album",
                f"{artist_name} studio album",
                f"{artist_name} full album",
                f"{artist_name} soundtrack"
            ]
            
            filtered_albums = []
            
            for search_query in search_queries:
                if len(filtered_albums) >= limit:
                    break
                    
                search_results = await self._execute_async(self.ytm.search, search_query, limit=limit * 2)
                
                # Filter results to only include albums by this specific artist
                for item in search_results:
                    # Only include items that are actually albums (not songs or playlists)
                    if item.get('resultType') == 'album':
                        # Check if the album has artists and if the target artist is in the list
                        artists = item.get('artists', [])
                        if isinstance(artists, list):
                            for artist in artists:
                                if isinstance(artist, dict) and artist.get('name'):
                                    if artist_name.lower() in artist.get('name', '').lower():
                                        # Check if this album is not already in the list
                                        album_id = item.get('browseId')
                                        if not any(a.get('browseId') == album_id for a in filtered_albums):
                                            filtered_albums.append(item)
                                            break
                        
                        # If we have enough albums, stop
                        if len(filtered_albums) >= limit:
                            break
            
            # Sort albums by year (latest first) and transform
            # Handle year comparison properly - convert to int for sorting
            def get_year_for_sorting(album):
                year = album.get('year')
                if year is None:
                    return 0
                try:
                    return int(year)
                except (ValueError, TypeError):
                    return 0
            
            sorted_albums = sorted(filtered_albums, key=get_year_for_sorting, reverse=True)
            return self._transform_albums_data(sorted_albums)
            
        except Exception as e:
            print(f"Error getting artist albums for {artist_id}: {e}")
            # Return empty list if there's an error
            return []

    def _transform_playlists_data(self, playlists_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform a list of playlists to our schema format."""
        transformed_playlists = []
        
        # Handle case where playlists_data might not be a list
        if not isinstance(playlists_data, list):
            print(f"Warning: playlists_data is not a list: {type(playlists_data)} - {playlists_data}")
            return []
        
        for playlist in playlists_data:
            # Handle case where playlist might not be a dictionary
            if not isinstance(playlist, dict):
                print(f"Warning: playlist is not a dictionary: {type(playlist)} - {playlist}")
                continue
            
            # Handle author field which might be a list or string
            author = playlist.get('author')
            if isinstance(author, list) and author:
                author = author[0].get('name', '') if isinstance(author[0], dict) else str(author[0])
            elif not author:
                author = None
            
            # Handle track_count - parse and validate
            track_count = self._parse_track_count(playlist.get('itemCount'))
            
            # Transform thumbnails
            thumbnails = []
            if playlist.get('thumbnails'):
                for thumb in playlist.get('thumbnails', []):
                    if isinstance(thumb, dict):
                        thumbnails.append({
                            "url": thumb.get('url'),
                            "width": thumb.get('width'),
                            "height": thumb.get('height')
                        })
            
            # Get playlist ID - try different fields
            playlist_id = playlist.get('playlistId') or playlist.get('browseId') or playlist.get('id')
            
            transformed_playlists.append({
                "id": playlist_id,
                "title": playlist.get('title', 'Unknown Playlist'),
                "description": playlist.get('description'),
                "author": author,
                "track_count": track_count,
                "thumbnails": thumbnails if thumbnails else None,
                "songs": []  # We don't include songs in the list view to keep it lightweight
            })
        
        return transformed_playlists

    def _transform_albums_data(self, albums_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform a list of albums to our schema format."""
        transformed_albums = []
        
        # Handle case where albums_data might not be a list
        if not isinstance(albums_data, list):
            print(f"Warning: albums_data is not a list: {type(albums_data)} - {albums_data}")
            return []
        
        for album in albums_data:
            # Handle case where album might not be a dictionary
            if not isinstance(album, dict):
                print(f"Warning: album is not a dictionary: {type(album)} - {album}")
                continue
            
            # Safely extract artist names
            artists = album.get('artists', [])
            artist_names = []
            if isinstance(artists, list):
                for artist in artists:
                    if isinstance(artist, dict) and artist.get('name'):
                        artist_names.append(artist['name'])
            
            artist_string = ", ".join(artist_names) if artist_names else "Unknown Artist"
            
            # Handle track_count - parse and validate
            # Try multiple possible field names for track count
            track_count = None
            for field in ['trackCount', 'track_count', 'itemCount', 'item_count']:
                track_count = self._parse_track_count(album.get(field))
                if track_count:
                    break
            
            # Transform thumbnails
            thumbnails = []
            if album.get('thumbnails'):
                for thumb in album.get('thumbnails', []):
                    if isinstance(thumb, dict):
                        thumbnails.append({
                            "url": thumb.get('url'),
                            "width": thumb.get('width'),
                            "height": thumb.get('height')
                        })
            
            # Get album ID - try different fields
            album_id = album.get('browseId') or album.get('id')
            
            transformed_albums.append({
                "id": album_id,
                "title": album.get('title', 'Unknown Album'),
                "artist": artist_string,
                "year": album.get('year'),
                "track_count": track_count,
                "thumbnails": thumbnails if thumbnails else None,
                "songs": []  # We don't include songs in the list view to keep it lightweight
            })
        
        return transformed_albums

    def _transform_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform YTM search results to our schema format."""
        transformed_results = []
        for item in results:
            result_type = item.get('resultType')
            transformed_item = None

            try:
                if result_type == 'song':
                    # Extract artist names from the artists array
                    artists = item.get('artists', [])
                    artist_names = [artist.get('name', '') for artist in artists if artist.get('name')]
                    artist_string = ", ".join(artist_names) if artist_names else "Unknown Artist"
                    
                    # Get video ID for stream URL and thumbnails
                    video_id = item.get('videoId')
                    
                    # Ensure title is not None
                    title = item.get('title')
                    if title is None:
                        title = "Unknown Title"
                    
                    # Transform thumbnails
                    thumbnails = []
                    if item.get('thumbnails'):
                        for thumb in item.get('thumbnails', []):
                            thumbnails.append({
                                "url": thumb.get('url'),
                                "width": thumb.get('width'),
                                "height": thumb.get('height')
                            })
                    
                    transformed_item = {
                        "type": "song",
                        "data": {
                            "id": video_id,
                            "title": title,
                            "artist": artist_string,
                            "album": item.get('album', {}).get('name') if item.get('album') else None,
                            "duration": item.get('duration'),
                            "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
                            "thumbnails": thumbnails if thumbnails else None,
                            "stream_url": None  # Will be populated later if needed
                        }
                    }
                elif result_type == 'album':
                    # Extract artist names from the artists array
                    artists = item.get('artists', [])
                    artist_names = [artist.get('name', '') for artist in artists if artist.get('name')]
                    artist_string = ", ".join(artist_names) if artist_names else "Unknown Artist"
                    
                    # Ensure title is not None
                    title = item.get('title')
                    if title is None:
                        title = "Unknown Album"
                    
                    # Handle track_count - convert to string if it's an integer
                    track_count = item.get('trackCount')
                    if isinstance(track_count, int):
                        track_count = str(track_count)
                    
                    # Transform thumbnails
                    thumbnails = []
                    if item.get('thumbnails'):
                        for thumb in item.get('thumbnails', []):
                            thumbnails.append({
                                "url": thumb.get('url'),
                                "width": thumb.get('width'),
                                "height": thumb.get('height')
                            })
                    
                    transformed_item = {
                        "type": "album",
                        "data": {
                            "id": item.get('browseId'),
                            "title": title,
                            "artist": artist_string,
                            "year": item.get('year'),
                            "track_count": track_count,
                            "thumbnails": thumbnails if thumbnails else None
                        }
                    }
                elif result_type == 'playlist':
                    # Handle author field which might be a list or string
                    author = item.get('author')
                    if isinstance(author, list) and author:
                        author = author[0].get('name', '') if isinstance(author[0], dict) else str(author[0])
                    elif not author:
                        author = None
                    
                    # Ensure title is not None
                    title = item.get('title')
                    if title is None:
                        title = "Unknown Playlist"
                    
                    # Handle track_count - parse and validate
                    track_count = self._parse_track_count(item.get('itemCount'))
                    
                    # Transform thumbnails
                    thumbnails = []
                    if item.get('thumbnails'):
                        for thumb in item.get('thumbnails', []):
                            thumbnails.append({
                                "url": thumb.get('url'),
                                "width": thumb.get('width'),
                                "height": thumb.get('height')
                            })
                    
                    # Get playlist ID - try different fields
                    playlist_id = item.get('playlistId') or item.get('browseId') or item.get('id')
                    
                    transformed_item = {
                        "type": "playlist",
                        "data": {
                            "id": playlist_id,
                            "title": title,
                            "author": author,
                            "track_count": track_count,
                            "thumbnails": thumbnails if thumbnails else None
                        }
                    }
                elif result_type == 'artist':
                    # For artist results, try multiple possible field names for artist name
                    artist_name = None
                    
                    # Try different possible field names for artist ID
                    artist_id = None
                    possible_id_fields = ['browseId', 'channelId', 'id', 'artistId']
                    for field in possible_id_fields:
                        artist_id = item.get(field)
                        if artist_id:
                            break
                    
                    # If no ID found in direct fields, try to extract from artists array
                    if not artist_id and item.get('artists'):
                        artists = item.get('artists', [])
                        if isinstance(artists, list) and artists:
                            # Get the first artist's ID
                            first_artist = artists[0]
                            if isinstance(first_artist, dict):
                                artist_id = first_artist.get('id')
                    

                    
                    # Try different possible field names for artist name
                    possible_name_fields = ['artist', 'name', 'title', 'author']
                    for field in possible_name_fields:
                        artist_name = item.get(field)
                        if artist_name:
                            break
                    
                    # If still no name found, try to extract from artists array
                    if not artist_name and item.get('artists'):
                        artists = item.get('artists', [])
                        if isinstance(artists, list) and artists:
                            artist_name = artists[0].get('name') if isinstance(artists[0], dict) else str(artists[0])
                    
                    # Ensure artist name is not None
                    if artist_name is None:
                        artist_name = "Unknown Artist"
                    
                    # Transform thumbnails
                    thumbnails = []
                    if item.get('thumbnails'):
                        for thumb in item.get('thumbnails', []):
                            thumbnails.append({
                                "url": thumb.get('url'),
                                "width": thumb.get('width'),
                                "height": thumb.get('height')
                            })
                    
                    transformed_item = {
                        "type": "artist",
                        "data": {
                            "id": artist_id,
                            "name": artist_name,
                            "thumbnails": thumbnails if thumbnails else None
                        }
                    }
                
                if transformed_item:
                    transformed_results.append(transformed_item)
            except Exception as e:
                print(f"Error transforming item {result_type}: {e}")
                print(f"Item data: {item}")
                continue
                
        return transformed_results

    def _transform_song_data(self, song_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform YTM song data to our schema format."""
        video_details = song_data.get('videoDetails', {})
        video_id = video_details.get('videoId')
        
        # Generate thumbnails from video ID
        thumbnails = []
        if video_id:
            thumbnails = [
                {
                    "url": f"https://i.ytimg.com/vi/{video_id}/default.jpg",
                    "width": 120,
                    "height": 90
                },
                {
                    "url": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
                    "width": 320,
                    "height": 180
                },
                {
                    "url": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                    "width": 480,
                    "height": 360
                },
                {
                    "url": f"https://i.ytimg.com/vi/{video_id}/sddefault.jpg",
                    "width": 640,
                    "height": 480
                },
                {
                    "url": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
                    "width": 1280,
                    "height": 720
                }
            ]
        
        # Ensure required fields are not None
        title = video_details.get('title')
        if title is None:
            title = "Unknown Title"
            
        artist = video_details.get('author')
        if artist is None:
            artist = "Unknown Artist"
        
        return {
            "id": video_id,
            "title": title,
            "artist": artist,
            "duration": video_details.get('lengthSeconds'),
            "thumbnails": thumbnails if thumbnails else None,
            "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None
        }

    def _transform_album_data(self, album_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform YTM album data to our schema format."""
        # Handle case where album_data might be a string or None
        if not isinstance(album_data, dict):
            print(f"Warning: album_data is not a dictionary: {type(album_data)} - {album_data}")
            return {
                "id": None,
                "title": "Unknown Album",
                "artist": "Unknown Artist",
                "year": None,
                "track_count": None,
                "tracks": []
            }
        
        # Safely extract artist names
        artists = album_data.get('artists', [])
        artist_names = []
        if isinstance(artists, list):
            for artist in artists:
                if isinstance(artist, dict) and artist.get('name'):
                    artist_names.append(artist['name'])
        
        artist_string = ", ".join(artist_names) if artist_names else "Unknown Artist"
        
        # Handle track_count - parse and validate
        track_count = self._parse_track_count(album_data.get('trackCount'))
        
        return {
            "id": album_data.get('audioPlaylistId'),
            "title": album_data.get('title', 'Unknown Album'),
            "artist": artist_string,
            "year": album_data.get('year'),
            "track_count": track_count,
            "songs": self._transform_songs_data(album_data.get('tracks', []))
        }

    def _transform_playlist_data(self, playlist_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform YTM playlist data to our schema format."""
        # Handle track_count - parse and validate
        track_count = self._parse_track_count(playlist_data.get('trackCount'))
        
        # Transform thumbnails
        thumbnails = []
        if playlist_data.get('thumbnails'):
            for thumb in playlist_data.get('thumbnails', []):
                if isinstance(thumb, dict):
                    thumbnails.append({
                        "url": thumb.get('url'),
                        "width": thumb.get('width'),
                        "height": thumb.get('height')
                    })
        
        # Ensure required fields are not None
        title = playlist_data.get('title')
        if title is None:
            title = "Unknown Playlist"
        
        return {
            "id": playlist_data.get('id'),
            "title": title,
            "description": playlist_data.get('description'),
            "author": playlist_data.get('author'),
            "track_count": track_count,
            "thumbnails": thumbnails if thumbnails else None,
            "songs": self._transform_songs_data(playlist_data.get('tracks', []))
        }

    def _transform_artist_data(self, artist_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform YTM artist data to our schema format."""
        # Transform thumbnails
        thumbnails = []
        if artist_data.get('thumbnails'):
            for thumb in artist_data.get('thumbnails', []):
                if isinstance(thumb, dict):
                    thumbnails.append({
                        "url": thumb.get('url'),
                        "width": thumb.get('width'),
                        "height": thumb.get('height')
                    })
        
        # Ensure required fields are not None
        name = artist_data.get('name')
        if name is None:
            name = "Unknown Artist"
        
        return {
            "id": artist_data.get('channelId'),
            "name": name,
            "description": artist_data.get('description'),
            "subscriber_count": artist_data.get('subscriberCount'),
            "thumbnails": thumbnails if thumbnails else None,
            "songs": self._transform_songs_data(artist_data.get('songs', {}).get('results', [])) if artist_data.get('songs') else []
        }

    def _transform_songs_data(self, songs_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform a list of songs to our schema format."""
        transformed_songs = []
        
        # Handle case where songs_data might not be a list
        if not isinstance(songs_data, list):
            print(f"Warning: songs_data is not a list: {type(songs_data)} - {songs_data}")
            return []
        
        for song in songs_data:
            # Handle case where song might not be a dictionary
            if not isinstance(song, dict):
                print(f"Warning: song is not a dictionary: {type(song)} - {song}")
                continue
                
            # Safely extract artist names
            artists = song.get('artists', [])
            artist_names = []
            if isinstance(artists, list):
                for artist in artists:
                    if isinstance(artist, dict) and artist.get('name'):
                        artist_names.append(artist['name'])
            
            artist_string = ", ".join(artist_names) if artist_names else "Unknown Artist"
            
            # Safely extract album name with multiple fallbacks
            album = song.get('album')
            album_name = None
            
            if isinstance(album, dict):
                album_name = album.get('name')
            elif isinstance(album, str):
                album_name = album
            elif album is None:
                # Try alternative album fields
                album_name = song.get('albumName') or song.get('album_name')
                
            # If still no album name, use title as fallback for single tracks
            if not album_name and song.get('title'):
                album_name = song.get('title')
            
            # Transform thumbnails
            thumbnails = []
            if song.get('thumbnails'):
                for thumb in song.get('thumbnails', []):
                    if isinstance(thumb, dict):
                        thumbnails.append({
                            "url": thumb.get('url'),
                            "width": thumb.get('width'),
                            "height": thumb.get('height')
                        })
            
            # If no thumbnails from API, generate them from video ID
            if not thumbnails and song.get('videoId'):
                video_id = song.get('videoId')
                # For now, use standard YouTube thumbnails as fallback
                # TODO: Implement proper YTM thumbnail fetching
                thumbnails = [
                    {
                        "url": f"https://i.ytimg.com/vi/{video_id}/default.jpg",
                        "width": 120,
                        "height": 90
                    },
                    {
                        "url": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
                        "width": 320,
                        "height": 180
                    },
                    {
                        "url": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                        "width": 480,
                        "height": 360
                    },
                    {
                        "url": f"https://i.ytimg.com/vi/{video_id}/sddefault.jpg",
                        "width": 640,
                        "height": 480
                    },
                    {
                        "url": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
                        "width": 1280,
                        "height": 720
                    }
                ]
            
            # Ensure required fields are not None
            title = song.get('title')
            if title is None:
                title = "Unknown Title"
            
            transformed_songs.append({
                "id": song.get('videoId'),
                "title": title,
                "artist": artist_string,
                "album": album_name,
                "duration": song.get('duration'),
                "thumbnails": thumbnails if thumbnails else None,
                "url": f"https://www.youtube.com/watch?v={song.get('videoId')}" if song.get('videoId') else None
            })
        return transformed_songs



    async def _add_stream_urls(self, results: List[Dict[str, Any]]):
        """
        Add stream URLs to song results.
        """
        for result in results:
            if result.get('type') == 'song' and result.get('data', {}).get('id'):
                video_id = result['data']['id']
                stream_url = await self.stream_service.get_stream_url(video_id)
                result['data']['stream_url'] = stream_url
 