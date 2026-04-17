import os
import pygame
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static
from textual.binding import Binding

class MusicPlayerApp(App):
    """A Cross-Platform TUI Music Player"""
    
    TITLE = "🎵 TUI Music Player 🎵"
    
    CSS = """
    Screen {
        background: $surface-darken-1;
    }
    DataTable {
        height: 1fr;
        margin: 1 2;
        border: round $primary;
        background: $surface;
    }
    #status {
        height: 3;
        margin: 0 2 1 2;
        dock: bottom;
        content-align: center middle;
        background: $panel;
        color: $text;
        border: round $secondary;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("p", "play", "Play", priority=True),
        Binding("space", "toggle_pause", "Pause/Resume", priority=True),
        Binding("n", "next", "Next", priority=True),
        Binding("b", "previous", "Previous", priority=True),
        Binding("q", "quit", "Quit", priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="song_list")
        yield Static("Status: Stopped", id="status")
        yield Footer()

    def on_mount(self) -> None:
        # Initialize pygame audio engine
        pygame.mixer.init()
        
        # Load songs
        self.song_dir = Path("songs")
        self.song_dir.mkdir(exist_ok=True)
        self.songs = [f.name for f in self.song_dir.glob("*.mp3")]
        self.songs.sort()
        
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("ID", "Song Name")
        for idx, song in enumerate(self.songs):
            table.add_row(str(idx + 1), song)
        
        self.current_index = 0 if self.songs else -1
        self.is_playing = False
        self.is_paused = False
        
        self.update_status()
        
        # Periodically check if the song has finished
        self.set_interval(1.0, self.check_music_end)

    def watch_current_index(self) -> None:
        if self.current_index != -1 and self.songs:
            table = self.query_one(DataTable)
            table.move_cursor(row=self.current_index)
            
    def action_play(self) -> None:
        if self.current_index != -1 and not self.is_playing and not self.is_paused:
            song_path = self.song_dir / self.songs[self.current_index]
            try:
                pygame.mixer.music.load(str(song_path))
                pygame.mixer.music.play()
                self.is_playing = True
                self.is_paused = False
                self.update_status()
            except pygame.error:
                pass # Optionally show error in status

    def action_toggle_pause(self) -> None:
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.is_paused = True
            self.update_status()
        elif self.is_paused:
            pygame.mixer.music.unpause()
            self.is_playing = True
            self.is_paused = False
            self.update_status()

    def action_next(self) -> None:
        if self.songs:
            self.current_index = (self.current_index + 1) % len(self.songs)
            self.is_playing = False
            self.is_paused = False
            pygame.mixer.music.stop()
            self.watch_current_index()
            self.action_play()

    def action_previous(self) -> None:
        if self.songs:
            self.current_index = (self.current_index - 1) % len(self.songs)
            self.is_playing = False
            self.is_paused = False
            pygame.mixer.music.stop()
            self.watch_current_index()
            self.action_play()

    def action_quit(self) -> None:
        pygame.mixer.quit()
        self.exit()

    def update_status(self) -> None:
        status_widget = self.query_one("#status", Static)
        if self.current_index == -1:
            status_widget.update("Status: No .mp3 files found in songs/ directory.")
            return

        song_name = self.songs[self.current_index]
        state = "Playing" if self.is_playing else ("Paused" if self.is_paused else "Stopped")
        status_widget.update(f"Status: {state} | Current Song: {song_name}")

    def check_music_end(self) -> None:
        # Pygame mixer music get_busy returns False when stopped or finished
        if self.is_playing and not pygame.mixer.music.get_busy():
            # Only go to next song if it actually stopped playing without user pause
            self.action_next()
            
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # User clicked or pressed enter on a row
        self.current_index = event.cursor_row
        self.is_playing = False
        self.is_paused = False
        pygame.mixer.music.stop()
        self.action_play()


if __name__ == "__main__":
    app = MusicPlayerApp()
    app.run()
