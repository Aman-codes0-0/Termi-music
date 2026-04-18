import os
from pathlib import Path

class FolderNotFoundError(Exception):
    """Raised when the provided folder does not exist or is invalid."""
    pass

class NoAudioFilesFoundError(Exception):
    """Raised when no audio files are found in the folder."""
    pass

def scan_folder(folder_path: str) -> list[str]:
    """Recursively scans a folder for audio files.
    
    Args:
        folder_path (str): The absolute or relative path to the directory.
        
    Returns:
        list[str]: A sorted list of absolute paths to discovered audio files.
    """
    path = Path(folder_path).resolve()
    
    if not path.exists() or not path.is_dir():
        raise FolderNotFoundError(f"Folder '{folder_path}' is invalid or does not exist.")
        
    supported_extensions = {".mp3", ".wav", ".flac", ".ogg"}
    songs = []
    
    # Recursively find all matching files
    for file in path.rglob("*"):
        if file.is_file() and file.suffix.lower() in supported_extensions:
            songs.append(str(file))
            
    if not songs:
        raise NoAudioFilesFoundError(f"No valid audio files found in '{folder_path}'.")
        
    songs.sort()
    return songs
