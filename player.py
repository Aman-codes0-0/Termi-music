import random

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

class BaseMusicPlayer:
    def __init__(self):
        self.playlist = []
        self.current_index = -1
        self.is_playing = False
        self.is_paused = False
        
        self.volume = 0.5
        self.is_muted = False
        self.is_shuffled = False
        self.is_repeating = False

    def load_playlist(self, songs: list) -> None:
        self.playlist = songs
        self.current_index = -1
        self.stop()

    def set_volume(self, val: float) -> None:
        self.volume = max(0.0, min(1.0, val))
        self._apply_volume()

    def toggle_mute(self) -> None:
        self.is_muted = not self.is_muted
        self._apply_volume()

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

    def get_current_song_name(self) -> str:
        if 0 <= self.current_index < len(self.playlist):
            return self.playlist[self.current_index].get("title", "Unknown")
        return "None"

    # -- Virtual Overrides --
    def _apply_volume(self) -> None: pass
    def play_local_file(self, index: int, filepath: str) -> None: pass
    def stop(self) -> None: pass
    def check_finished_naturally(self) -> bool: return False
    def get_current_pos(self) -> float: return 0.0
    def quit(self) -> None: pass


class PygamePlayer(BaseMusicPlayer):
    def __init__(self):
        super().__init__()
        if HAS_PYGAME:
            pygame.mixer.init()
        self._apply_volume()

    def _apply_volume(self) -> None:
        if not HAS_PYGAME: return
        try:
            if self.is_muted:
                pygame.mixer.music.set_volume(0.0)
            else:
                pygame.mixer.music.set_volume(self.volume)
        except Exception:
            pass

    def play_local_file(self, index: int, filepath: str) -> None:
        if not HAS_PYGAME: return
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            self.current_index = index
            self.is_playing = True
            self.is_paused = False
        except Exception:
            pass

    def stop(self) -> None:
        if not HAS_PYGAME: return
        try:
            pygame.mixer.music.stop()
        except Exception: pass
        self.is_playing = False
        self.is_paused = False

    def toggle_pause(self) -> None:
        if not HAS_PYGAME: return
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

    def check_finished_naturally(self) -> bool:
        if not HAS_PYGAME: return False
        if self.is_playing and not pygame.mixer.music.get_busy() and not self.is_paused:
            self.is_playing = False
            return True
        return False

    def get_current_pos(self) -> float:
        if not HAS_PYGAME: return 0.0
        # pygame.mixer.music.get_pos() returns ms since playback started
        pos_ms = pygame.mixer.music.get_pos()
        if pos_ms < 0: return 0.0
        return pos_ms / 1000.0

    def quit(self) -> None:
        if not HAS_PYGAME: return
        pygame.mixer.quit()


# Factory Return
def MusicPlayer():
    return PygamePlayer()
