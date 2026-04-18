from ytmusicapi import YTMusic
import yt_dlp
import os
import threading

ytmusic = YTMusic()
def is_termux() -> bool:
    return 'com.termux' in os.environ.get('PREFIX', '') or 'ANDROID_ROOT' in os.environ

def get_cache_dir() -> str:
    """Returns a writable cache directory, prioritized for Termux/Mobile."""
    if is_termux():
        # Use $HOME/.cache/tui_music_player in Termux
        base = os.environ.get('HOME', '/data/data/com.termux/files/home')
        path = os.path.join(base, '.cache', 'tui_music_cache')
    else:
        path = "/tmp/tui_music_cache"
    
    if not os.path.exists(path):
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            # Fallback to local directory if all else fails
            path = os.path.join(os.getcwd(), ".tui_music_cache")
            os.makedirs(path, exist_ok=True)
    return path

CACHE_DIR = get_cache_dir()
download_lock = threading.Lock()

def get_ffmpeg_path() -> str:
    if is_termux():
        return 'ffmpeg' # Native Android binaries assuming `pkg install ffmpeg` is ready
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return 'ffmpeg'

def ensure_cache():
    # Cache directory is now ensured during get_cache_dir() initialization
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)

def _parse_songs_from_results(results: list) -> list:
    """Helper: convert raw ytmusicapi results to our song dict format."""
    songs = []
    for r in results:
        artists = ", ".join([a.get('name', 'Unknown') for a in r.get('artists', [])])
        duration = r.get('duration', '0:00') or '0:00'
        title = r.get('title', 'Unknown Title')
        videoId = r.get('videoId')
        if videoId:
            songs.append({
                "title": title,
                "artists": artists,
                "duration": duration,
                "videoId": videoId
            })
    return songs


def _get_artist_songs(query: str) -> list:
    """Try to find an artist by query and return all their songs.
    Returns empty list if no artist match found."""
    try:
        # Search for the artist
        artist_results = ytmusic.search(query, filter="artists", limit=3)
        if not artist_results:
            return []

        # Pick the top artist result
        artist = artist_results[0]
        artist_id = artist.get('browseId')
        if not artist_id:
            return []

        # Fetch artist page
        artist_data = ytmusic.get_artist(artist_id)
        songs = []

        # Get songs from the artist's songs section
        songs_data = artist_data.get('songs', {})
        songs_browse_id = songs_data.get('browseId')
        if songs_browse_id:
            # Fetch all songs via the dedicated songs playlist
            try:
                playlist = ytmusic.get_artist_albums(artist_id, params=songs_data.get('params', ''))
            except Exception:
                playlist = None

            # Fallback: use the songs directly available on artist page
            raw_songs = songs_data.get('results', [])
            songs.extend(_parse_songs_from_results(raw_songs))

        # Also grab from albums to get more songs
        albums_data = artist_data.get('albums', {})
        album_results = albums_data.get('results', [])[:5]  # Top 5 albums
        for album in album_results:
            album_id = album.get('browseId')
            if not album_id:
                continue
            try:
                album_data = ytmusic.get_album(album_id)
                raw_tracks = album_data.get('tracks', [])
                songs.extend(_parse_songs_from_results(raw_tracks))
            except Exception:
                continue

        # Deduplicate by videoId
        seen = set()
        unique_songs = []
        for s in songs:
            if s['videoId'] not in seen:
                seen.add(s['videoId'])
                unique_songs.append(s)

        return unique_songs
    except Exception:
        return []


def search_songs(query: str, limit: int = 20) -> list:
    """Search for songs. If query matches an artist, return all their songs.
    Otherwise fall back to a regular song search."""

    # First try artist-based search
    artist_songs = _get_artist_songs(query)
    if artist_songs:
        return artist_songs

    # Fallback: regular song search
    results = ytmusic.search(query, filter="songs", limit=limit)
    return _parse_songs_from_results(results)

def download_audio(video_id: str) -> str:
    """Download audio to cache and return the filepath.
    Uses concurrency locks to prevent race conditions during background pre-fetching!"""
    with download_lock:
        ensure_cache()
        out_path = os.path.join(CACHE_DIR, f"{video_id}.mp3")
        
        if os.path.exists(out_path):
            return out_path
            
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(CACHE_DIR, f"{video_id}.%(ext)s"),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'ffmpeg_location': get_ffmpeg_path(),
            'quiet': True,
            'no_warnings': True,
            'noprogress': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            if "ffmpeg" in str(e).lower():
                raise RuntimeError("FFmpeg not found. Please install it using 'pkg install ffmpeg' in Termux.")
            raise RuntimeError(f"Download failed: {str(e)}")
            
        return out_path
