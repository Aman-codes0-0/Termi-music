import os
import pygame

class MusicPlayer:
    """Encapsulates the Pygame audio playback logic."""
    def __init__(self):
        pygame.mixer.init()
        self.playlist: list[str] = []
        self.current_index: int = -1
        self.is_playing: bool = False
        self.is_paused: bool = False

    def load_playlist(self, songs: list[str]) -> None:
        """Loads a new list of absolute file paths to play."""
        self.playlist = songs
        self.current_index = 0 if songs else -1
        self.stop()

    def play(self, index: int) -> None:
        """Plays a target song index from the playlist."""
        if index < 0 or index >= len(self.playlist):
            return
            
        self.current_index = index
        try:
            pygame.mixer.music.load(self.playlist[self.current_index])
            pygame.mixer.music.play()
            self.is_playing = True
            self.is_paused = False
        except pygame.error:
            pass # Fail silently as this is called sequentially

    def toggle_pause(self) -> None:
        """Toggles current loaded music between Play and Pause."""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.is_paused = True
        elif self.is_paused:
            pygame.mixer.music.unpause()
            self.is_playing = True
            self.is_paused = False
        elif self.current_index != -1:
            # If completely stopped but we have an index, just play it
            self.play(self.current_index)

    def stop(self) -> None:
        """Completely halts parsing audio."""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False

    def next(self) -> None:
        if not self.playlist:
            return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.stop()
        self.play(self.current_index)

    def previous(self) -> None:
        if not self.playlist:
            return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.stop()
        self.play(self.current_index)
        
    def check_finished_naturally(self) -> bool:
        """Returns True if the music stream hit its end without user stoppage."""
        return self.is_playing and not pygame.mixer.music.get_busy()
        
    def get_current_song_name(self) -> str:
        """Returns the base filename of the playing song."""
        if self.current_index == -1 or not self.playlist:
            return ""
        return os.path.basename(self.playlist[self.current_index])
        
    def quit(self) -> None:
        pygame.mixer.quit()
