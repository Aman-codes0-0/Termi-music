import pygame
import random

class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.playlist = [] # List of dictionary objects containing videoId
        self.current_index = -1
        self.is_playing = False
        self.is_paused = False
        
        # New V2.0 States
        self.volume = 0.5
        self.is_muted = False
        self.is_shuffled = False
        self.is_repeating = False
        
        pygame.mixer.music.set_volume(self.volume)

    # -- V2.0 Controls --
    def set_volume(self, val: float) -> None:
        self.volume = max(0.0, min(1.0, val))
        if not self.is_muted:
            pygame.mixer.music.set_volume(self.volume)

    def toggle_mute(self) -> None:
        self.is_muted = not self.is_muted
        if self.is_muted:
            pygame.mixer.music.set_volume(0.0)
        else:
            pygame.mixer.music.set_volume(self.volume)

    def toggle_shuffle(self) -> None:
        self.is_shuffled = not self.is_shuffled

    def toggle_repeat(self) -> None:
        self.is_repeating = not self.is_repeating

    def get_next_index(self) -> int:
        if not self.playlist:
            return -1
        if self.is_repeating and self.current_index != -1:
            return self.current_index
        if self.is_shuffled:
            return random.randint(0, len(self.playlist) - 1)
        return (self.current_index + 1) % len(self.playlist)

    def get_previous_index(self) -> int:
        if not self.playlist:
            return -1
        if self.is_repeating and self.current_index != -1:
            return self.current_index
        if self.is_shuffled:
            return random.randint(0, len(self.playlist) - 1)
        return (self.current_index - 1) % len(self.playlist)

    # -- End V2.0 Controls --

    def load_playlist(self, songs: list) -> None:
        self.playlist = songs
        self.current_index = -1
        self.stop()

    def play_local_file(self, index: int, filepath: str) -> None:
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            self.current_index = index
            self.is_playing = True
            self.is_paused = False
        except Exception as e:
            pass

    def stop(self) -> None:
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False

    def toggle_pause(self) -> None:
        if not self.is_playing and not self.is_paused:
            return
            
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.is_playing = True
        else:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False

    def get_current_song_name(self) -> str:
        if 0 <= self.current_index < len(self.playlist):
            return self.playlist[self.current_index].get("title", "Unknown")
        return "None"

    def check_finished_naturally(self) -> bool:
        # If the music was playing, but now is not busy, and not paused, it finished naturally!
        if self.is_playing and not pygame.mixer.music.get_busy() and not self.is_paused:
            self.is_playing = False
            return True
        return False

    def quit(self) -> None:
        pygame.mixer.quit()
