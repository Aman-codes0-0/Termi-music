from ytmusicapi import YTMusic
import yt_dlp
import os
import shutil
import threading

ytmusic = YTMusic()
def get_cache_dir() -> str:
    """Returns a writable cache directory."""
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
        
        # Try to get duration from multiple fields
        duration = r.get('duration')
        if not duration:
            seconds = r.get('duration_seconds')
            if seconds:
                duration = f"{seconds // 60}:{seconds % 60:02d}"
            else:
                duration = '0:00'
        
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
            # Use the songs directly available on artist page
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
    """Search for songs.
    
    We prioritize regular song search (filter='songs') because it provides 
    the best metadata (like durations) and ensures we get audio tracks 
    rather than just video results.
    """
    # 1. Direct song search (Best results)
    results = ytmusic.search(query, filter="songs", limit=limit)
    songs = _parse_songs_from_results(results)
    
    if len(songs) >= 5: # If we got a decent amount of results, stick with them
        return songs

    # 2. Fallback: Try artist-based search if regular search is sparse
    artist_songs = _get_artist_songs(query)
    if artist_songs:
        # Merge results, prioritizing the direct ones
        seen = {s['videoId'] for s in songs}
        for s in artist_songs:
            if s['videoId'] not in seen:
                songs.append(s)
                seen.add(s['videoId'])
                
    return songs[:limit]

def _build_ydl_opts(video_id: str, cookies_from_browser: str | None = None) -> dict:
    """Build yt-dlp options dict, optionally with browser cookie extraction."""
    opts = {
        # Simple fallback chain: prefer audio-only streams, accept video+audio
        # as a last resort so we always find *something* to download.
        'format': 'bestaudio/best',
        'format_sort': ['abr', 'asr', 'ext'],
        'outtmpl': os.path.join(CACHE_DIR, f"{video_id}.%(ext)s"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'ffmpeg_location': get_ffmpeg_path(),
        # Use the Android client — exposes more formats and is less restricted
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
    }
    if cookies_from_browser:
        opts['cookiesfrombrowser'] = (cookies_from_browser,)
    return opts


def download_audio(video_id: str) -> str:
    """Download audio to cache and return the filepath.

    Automatically passes browser cookies to yt-dlp so YouTube doesn't
    reject the request as a bot.  Tries Chrome first, then Firefox, and
    finally falls back to a cookie-less attempt.

    Uses a concurrency lock to prevent race conditions during background
    pre-fetching.
    """
    with download_lock:
        ensure_cache()
        out_path = os.path.join(CACHE_DIR, f"{video_id}.mp3")

        if os.path.exists(out_path):
            return out_path

        url = f"https://www.youtube.com/watch?v={video_id}"

        # Browsers to try in order; None = no cookies (last resort)
        browsers_to_try: list[str | None] = ["chrome", "firefox", None]

        last_error: Exception | None = None
        for browser in browsers_to_try:
            try:
                ydl_opts = _build_ydl_opts(video_id, browser)
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                # If download succeeded the file now exists – return it
                return out_path
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                if "ffmpeg" in err_str:
                    raise RuntimeError(
                        "FFmpeg not found. Please make sure ffmpeg is installed."
                    ) from e
                # If any error occurs (format not available, bot detection, etc.)
                # just log it to last_error and let the loop continue to the next fallback.
                continue

        raise RuntimeError(f"Download failed: {str(last_error)}")

def clear_cache() -> None:
    """Removes all downloaded audio files in the cache directory."""
    if os.path.exists(CACHE_DIR):
        try:
            shutil.rmtree(CACHE_DIR)
        except Exception:
            pass
