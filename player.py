import pygame

class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.playlist = [] # List of dictionary objects containing videoId
        self.current_index = -1
        self.is_playing = False
        self.is_paused = False

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
