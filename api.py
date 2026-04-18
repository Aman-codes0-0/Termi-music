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

def search_songs(query: str, limit: int = 20):
    """Search for songs returning a list of dictionaries with metadata."""
    results = ytmusic.search(query, filter="songs", limit=limit)
    songs = []
    
    for r in results:
        artists = ", ".join([a.get('name', 'Unknown') for a in r.get('artists', [])])
        duration = r.get('duration', '0:00')
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
