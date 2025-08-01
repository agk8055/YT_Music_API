from pydantic import BaseModel
from typing import List, Optional
from .common import Thumbnail
from .song import Song
from .playlist import Playlist
from .album import Album

class Artist(BaseModel):
    id: Optional[str] = None  # Made optional to handle None values
    name: str
    description: Optional[str] = None
    subscriber_count: Optional[int] = None
    thumbnails: Optional[List[Thumbnail]] = None

class ArtistResponse(BaseModel):
    artist: Artist

class ArtistSongsResponse(BaseModel):
    songs: List[Song]

class ArtistPlaylistsResponse(BaseModel):
    playlists: List[Playlist]

class ArtistAlbumsResponse(BaseModel):
    albums: List[Album] 