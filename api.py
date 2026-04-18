from ytmusicapi import YTMusic
import yt_dlp
import os
import imageio_ffmpeg
import threading

ytmusic = YTMusic()
CACHE_DIR = "/tmp/tui_music_cache"
download_lock = threading.Lock()

def ensure_cache():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

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
            'ffmpeg_location': imageio_ffmpeg.get_ffmpeg_exe(),
            'quiet': True,
            'no_warnings': True,
            'noprogress': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        return out_path
