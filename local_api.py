from pathlib import Path
from tinytag import TinyTag

def scan_local_directory(directory_path: str) -> list:
    """Recursively scan directory for audio files and extract metadata."""
    supported_extensions = {'.mp3', '.flac', '.wav', '.m4a', '.ogg'}
    results = []
    
    path = Path(directory_path).expanduser()
    if not path.exists() or not path.is_dir():
        return results

    # Limit search to avoid hanging on massive directories
    count = 0
    max_files = 500

    for file_path in path.rglob('*'):
        if file_path.suffix.lower() in supported_extensions:
            try:
                tag = TinyTag.get(str(file_path))
                
                # Format duration to MM:SS
                duration_sec = int(tag.duration) if tag.duration else 0
                duration_str = f"{duration_sec // 60}:{duration_sec % 60:02d}"
                
                results.append({
                    "title": tag.title or file_path.stem,
                    "artists": tag.artist or "Unknown Artist",
                    "duration": duration_str,
                    "videoId": str(file_path.absolute()), # we use absolute path as videoId for local files
                    "is_local": True
                })
                
                count += 1
                if count >= max_files:
                    break
            except Exception:
                continue
                
    return results
