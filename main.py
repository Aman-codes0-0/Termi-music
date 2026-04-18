import os
import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static, Input, OptionList
from textual.widgets.option_list import Option
from textual.binding import Binding
from textual.screen import ModalScreen
from textual import work

from api import search_songs, download_audio
from player import MusicPlayer

CONFIG_FILE = "config.json"

def load_theme() -> str:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("theme", "textual-dark")
        except:
            pass
    return "textual-dark"

def save_theme(theme_name: str) -> None:
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"theme": theme_name}, f)
    except:
        pass

class ThemeSelector(ModalScreen):
    """Modal screen that shows all available themes."""
    
    BINDINGS = [Binding("escape", "dismiss_modal", "Cancel")]
    
    CSS = """
    ThemeSelector {
        align: center middle;
    }
    #theme_list {
        width: 50%;
        height: 60%;
        border: solid $secondary;
        background: $surface;
    }
    """
    
    def compose(self) -> ComposeResult:
        themes = list(self.app.available_themes.keys())
        themes.sort()
        yield OptionList(*[Option(str(t), id=str(t)) for t in themes], id="theme_list")

    def on_mount(self) -> None:
        list_widget = self.query_one(OptionList)
        list_widget.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        selected_theme = event.option.id
        self.app.theme = selected_theme
        save_theme(selected_theme)
        self.dismiss()

    def action_dismiss_modal(self) -> None:
        self.dismiss()

class MusicPlayerApp(App):
    """A Cross-Platform TUI Music Player"""
    
    TITLE = "🎵 Cloud TUI Music Player 🎵"
    ENABLE_COMMAND_PALETTE = False
    
    CSS = """
    Screen {
        background: $surface-darken-1;
    }
    Input {
        dock: top;
        margin: 1 2 0 2;
        border: tall $secondary;
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
        Binding("+", "volume_up", "Vol+", priority=True),
        Binding("-", "volume_down", "Vol-", priority=True),
        Binding("m", "toggle_mute", "Mute", priority=True),
        Binding("/", "focus_search", "Search", priority=True),
        Binding("escape", "focus_table", "List", priority=True, show=False),
        Binding("s", "toggle_shuffle", "Shuffle", priority=True),
        Binding("r", "toggle_repeat", "Repeat", priority=True),
        Binding("d", "select_theme", "Themes", priority=True),
        Binding("q", "quit", "Quit", priority=True),
    ]

    def get_compact_css(self) -> str:
        """Returns compact CSS for Termux/Mobile."""
        return """
        Input {
            margin: 0 1;
            border: tall $secondary;
        }
        DataTable {
            margin: 0 1;
            border: none;
        }
        #status {
            height: 2;
            margin: 0;
            border: none;
            background: $surface;
            text-style: none;
            font-size: 80%;
        }
        """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Search YouTube Music...", id="search_input")
        yield DataTable(id="song_list")
        yield Static("Status: Ready", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.theme = load_theme()
        from api import is_termux
        if is_termux():
            self.add_class("compact-mode")
            # Inject compact CSS
            self.app.stylesheet.add_source(self.get_compact_css())
            
        self.player = MusicPlayer()
        self.active_query = ""
        
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        
        if is_termux():
            table.add_columns("Artist", "Song")
        else:
            table.add_columns("ID", "Artist", "Song Name", "Duration")
        
        self.set_interval(1.0, self.check_music_end)
        
    @work(exclusive=True, thread=True)
    def handle_search(self, query: str) -> None:
        self.app.call_from_thread(self.notify, f"Searching for '{query}'...")
        try:
            results = search_songs(query, limit=15)
            self.app.call_from_thread(self.populate_table, query, results)
        except Exception as e:
            self.app.call_from_thread(self.notify, f"Search Error: {str(e)}", severity="error")

    def populate_table(self, query: str, results: list) -> None:
        self.active_query = query
        self.player.load_playlist(results)
        
        table = self.query_one(DataTable)
        table.clear()
        from api import is_termux
        for idx, song in enumerate(results):
            if is_termux():
                # Shorten artist names for mobile
                artist = song["artists"].split(",")[0][:15]
                table.add_row(artist, song["title"])
            else:
                table.add_row(str(idx + 1), song["artists"], song["title"], song["duration"])
            
        self.notify(f"Found {len(results)} results!", title="Search Complete")
        self.update_status()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if query:
            self.handle_search(query)
            
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.player.stop()
        self.fetch_and_play(event.cursor_row)

    @work(exclusive=True, thread=True)
    def fetch_and_play(self, index: int) -> None:
        if index < 0 or index >= len(self.player.playlist): return
        
        song = self.player.playlist[index]
        self.app.call_from_thread(self.notify, f"Downloading: {song['title']}", title="Loading Cloud Track")
        
        try:
            filepath = download_audio(song["videoId"])
            self.app.call_from_thread(self.execute_play, index, filepath)
        except Exception as e:
            self.app.call_from_thread(self.notify, f"Download failed: {str(e)}", severity="error")

    def execute_play(self, index: int, filepath: str) -> None:
        self.player.play_local_file(index, filepath)
        table = self.query_one(DataTable)
        table.move_cursor(row=index)
        self.update_status()
        
        # Secretly download the next track in the queue directly behind the scenes!
        self.prefetch_next_song()

    @work(exclusive=True, thread=True)
    def prefetch_next_song(self) -> None:
        next_idx = self.player.get_next_index()
        if next_idx < 0 or next_idx >= len(self.player.playlist):
            return
            
        song = self.player.playlist[next_idx]
        try:
            download_audio(song["videoId"]) # Caches the raw file silently in background
        except:
            pass

    # -- Keybindings Actions --
    def action_play(self) -> None:
        if not self.player.is_playing and not self.player.is_paused:
            table = self.query_one(DataTable)
            if table.cursor_row is not None and self.player.playlist:
                self.fetch_and_play(table.cursor_row)
        else:
            self.update_status()

    def action_toggle_pause(self) -> None:
        self.player.toggle_pause()
        self.update_status()

    def action_next(self) -> None:
        if not self.player.playlist: return
        self.fetch_and_play(self.player.get_next_index())

    def action_previous(self) -> None:
        if not self.player.playlist: return
        self.fetch_and_play(self.player.get_previous_index())

    def action_volume_up(self) -> None:
        self.player.set_volume(self.player.volume + 0.1)
        self.update_status()

    def action_volume_down(self) -> None:
        self.player.set_volume(self.player.volume - 0.1)
        self.update_status()

    def action_toggle_mute(self) -> None:
        self.player.toggle_mute()
        self.update_status()
        
    def action_focus_search(self) -> None:
        self.query_one("#search_input", Input).focus()

    def action_focus_table(self) -> None:
        self.query_one(DataTable).focus()

    def action_toggle_shuffle(self) -> None:
        self.player.toggle_shuffle()
        self.update_status()

    def action_toggle_repeat(self) -> None:
        self.player.toggle_repeat()
        self.update_status()

    def action_select_theme(self) -> None:
        self.push_screen(ThemeSelector())

    def action_quit(self) -> None:
        self.player.quit()
        self.exit()

    def update_status(self) -> None:
        status_widget = self.query_one("#status", Static)
        
        if not self.player.playlist:
            status_widget.update("Status: Start by searching above!")
            return

        vol_pct = int(self.player.volume * 100)
        vol_state = "MUTED" if self.player.is_muted else f"Vol: {vol_pct}%"
        modes = []
        if self.player.is_shuffled: modes.append("Shuffle")
        if self.player.is_repeating: modes.append("Repeat")
        mode_str = f"[{' | '.join(modes)}] | " if modes else ""

        song_name = self.player.get_current_song_name()
        state = "Playing" if self.player.is_playing else ("Paused" if self.player.is_paused else "Stopped")
        
        from api import is_termux
        if is_termux():
            status = f"{state} | {vol_state} | {song_name[:20]}"
        else:
            status = f"Query: {self.active_query} | {len(self.player.playlist)} Results | {state} | {vol_state} | {mode_str}Song: {song_name}"
        status_widget.update(status)

    def check_music_end(self) -> None:
        if self.player.check_finished_naturally():
            self.action_next()

if __name__ == "__main__":
    app = MusicPlayerApp()
    app.run()
