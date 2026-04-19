import os
import json
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static, Input, OptionList, ProgressBar, DirectoryTree, Button, Label
from textual.containers import Horizontal, Vertical
from textual.widgets.option_list import Option
from textual.binding import Binding
from textual.screen import ModalScreen
from textual import work
from pathlib import Path

from api import search_songs, download_audio
from player import MusicPlayer

CONFIG_FILE = "config.json"

def load_theme() -> str:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("theme", "textual-dark")
        except Exception:
            pass
    return "textual-dark"

def save_theme(theme_name: str) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"theme": theme_name}, f)
    except Exception:
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

class FolderSelector(ModalScreen):
    """Modal screen that asks for a folder path."""
    
    BINDINGS = [Binding("escape", "dismiss_modal", "Cancel")]
    
    CSS = """
    FolderSelector {
        align: center middle;
    }
    #folder_container {
        width: 80%;
        height: 80%;
        padding: 1 2;
        border: solid $secondary;
        background: $surface;
    }
    DirectoryTree {
        height: 1fr;
        border: tall $background;
        margin: 1 0;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Vertical(id="folder_container"):
            yield Label("Navigate or enter the path to your Local Music folder:")
            yield DirectoryTree(str(Path.home()))
            yield Input(value=str(Path.home() / "Music"), id="folder_input")
            yield Button("Scan Folder", id="scan_btn", variant="primary")
            
    def on_mount(self) -> None:
        self.query_one("#folder_input", Input).focus()
        
    def on_tree_node_highlighted(self, event) -> None:
        if event.node.data and hasattr(event.node.data, "path"):
            self.query_one("#folder_input", Input).value = str(event.node.data.path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "scan_btn":
            path = self.query_one("#folder_input", Input).value
            self.dismiss(path)
            
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "folder_input":
            self.dismiss(event.value)

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)

class ModeSelector(ModalScreen):
    """Modal screen that asks for startup mode."""
    
    BINDINGS = [Binding("escape", "dismiss_modal", "Cancel")]
    
    CSS = """
    ModeSelector {
        align: center middle;
    }
    #mode_container {
        width: 40%;
        height: auto;
        padding: 1 2;
        border: solid $secondary;
        background: $surface;
    }
    Button {
        width: 100%;
        margin: 1 0;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Vertical(id="mode_container"):
            yield Label("[b]Select Startup Mode:[/b]")
            yield Button("Local Music", id="btn_local", variant="primary")
            yield Button("Online Streaming", id="btn_online", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_local":
            self.dismiss("local")
        elif event.button.id == "btn_online":
            self.dismiss("online")

    def action_dismiss_modal(self) -> None:
        self.dismiss("online")

class MusicPlayerApp(App):
    """A Cross-Platform TUI Music Player"""
    
    TITLE = "🎵 Cloud TUI Music Player 🎵"
    ENABLE_COMMAND_PALETTE = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.theme = "textual-dark"
        self.player = None
        self.active_query = ""
        self.search_results = []
        self.mode = "online"
        self.local_songs = []
    
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
    #bottom_bar {
        dock: bottom;
        height: 9;
        margin: 0 2;
    }
    #progress_container {
        height: 3;
        layout: horizontal;
        align: left middle;
    }
    #time_display {
        width: 16;
        color: $accent;
        text-style: bold;
        background: $surface;
    }
    ProgressBar {
        width: 1fr;
    }
    #status {
        height: 3;
        background: $panel;
        color: $text;
        border: round $secondary;
        content-align: center middle;
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

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Search YouTube Music...", id="search_input")
        yield DataTable(id="song_list")
        with Vertical(id="bottom_bar"):
            with Horizontal(id="progress_container"):
                yield Static("00:00 / 00:00", id="time_display")
                yield ProgressBar(show_eta=False, show_percentage=False)
            yield Static("Status: Ready", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.theme = load_theme()
        self.player = MusicPlayer()
        self.active_query = ""
        self.search_results = []
        
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        
        table.add_column("ID", width=4)
        table.add_column("Artist", width=25)
        table.add_column("Song Name", width=40)
        table.add_column("Duration", width=10)
        
        self.set_interval(1.0, self.check_music_end)
        self.push_screen(ModeSelector(), self.handle_mode_selection)

    def handle_mode_selection(self, mode: str | None) -> None:
        if mode == "local":
            self.ask_for_folder()
        else:
            self.switch_to_online_mode()
        
    @work(exclusive=True, thread=True)
    def handle_search(self, query: str) -> None:
        if self.mode == "local":
            self.app.call_from_thread(self.filter_local, query)
        else:
            self.app.call_from_thread(self.notify, f"Searching for '{query}'...")
            try:
                results = search_songs(query, limit=50)
                self.app.call_from_thread(self.populate_table, query, results)
            except Exception as e:
                self.app.call_from_thread(self.notify, f"Search Error: {str(e)}", severity="error")

    def filter_local(self, query: str) -> None:
        q = query.lower()
        filtered = [s for s in self.local_songs if q in s["title"].lower() or q in s["artists"].lower()]
        self.populate_table(query, filtered)

    def populate_table(self, query: str, results: list) -> None:
        self.active_query = query
        self.search_results = results
        
        table = self.query_one(DataTable)
        table.clear()
        for idx, song in enumerate(results):
            table.add_row(str(idx + 1), song["artists"], song["title"], song["duration"])
            
        self.notify(f"Found {len(results)} results!", title="Search Complete")
        self.update_status()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if query:
            self.handle_search(query)
            
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if self.player.playlist is not self.search_results:
            self.player.load_playlist(self.search_results)
        else:
            self.player.stop()
        self.fetch_and_play(event.cursor_row)

    @work(exclusive=True, thread=True)
    def fetch_and_play(self, index: int) -> None:
        if index < 0 or index >= len(self.player.playlist): return
        
        song = self.player.playlist[index]
        if song.get("is_local"):
            self.app.call_from_thread(self.notify, f"Playing: {song['title']}", title="Local Track")
            filepath = song["videoId"]
            self.app.call_from_thread(self.execute_play, index, filepath)
        else:
            self.app.call_from_thread(self.notify, f"Downloading: {song['title']}", title="Loading Cloud Track")
            try:
                filepath = download_audio(song["videoId"])
                self.app.call_from_thread(self.execute_play, index, filepath)
            except Exception as e:
                self.app.call_from_thread(self.notify, f"Download failed: {str(e)}", severity="error")

    def execute_play(self, index: int, filepath: str) -> None:
        self.player.play_local_file(index, filepath)
        if self.player.playlist is self.search_results:
            table = self.query_one(DataTable)
            try:
                table.move_cursor(row=index)
            except Exception:
                pass
        self.update_status()
        
        # Secretly download the next track in the queue directly behind the scenes!
        self.prefetch_next_song()

    @work(exclusive=True, thread=True)
    def prefetch_next_song(self) -> None:
        next_idx = self.player.get_next_index()
        if next_idx < 0 or next_idx >= len(self.player.playlist):
            return
            
        song = self.player.playlist[next_idx]
        if song.get("is_local"): return
        
        try:
            download_audio(song["videoId"]) # Caches the raw file silently in background
        except Exception:
            pass

    # -- Keybindings Actions --
    def action_play(self) -> None:
        if not self.player.is_playing and not self.player.is_paused:
            table = self.query_one(DataTable)
            if table.cursor_row is not None and self.search_results:
                if self.player.playlist is not self.search_results:
                    self.player.load_playlist(self.search_results)
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

    def ask_for_folder(self) -> None:
        def check_folder(path: str | None) -> None:
            if path:
                self.notify(f"Scanning {path}...", title="Local Mode")
                self.scan_folder_background(path)
            else:
                self.switch_to_online_mode()

        self.push_screen(FolderSelector(), check_folder)

    @work(exclusive=True, thread=True)
    def scan_folder_background(self, path: str) -> None:
        from local_api import scan_local_directory
        results = scan_local_directory(path)
        self.app.call_from_thread(self.switch_to_local_mode, results, path)
            
    def switch_to_local_mode(self, results: list, path: str) -> None:
        self.mode = "local"
        self.local_songs = results
        self.active_query = ""
        search_input = self.query_one("#search_input", Input)
        search_input.value = ""
        search_input.placeholder = f"Search {path}..."
        self.populate_table("", self.local_songs)
        self.notify(f"Found {len(results)} local files.", title="Local Mode")
        
    def switch_to_online_mode(self) -> None:
        self.mode = "online"
        self.active_query = ""
        self.search_results = []
        search_input = self.query_one("#search_input", Input)
        search_input.value = ""
        search_input.placeholder = "Search YouTube Music..."
        self.query_one(DataTable).clear()
        self.update_status()

    async def action_quit(self) -> None:
        self.player.quit()
        from api import clear_cache
        clear_cache()
        self.exit()

    def parse_duration(self, duration_str) -> int:
        """Converts MM:SS or HH:MM:SS to total seconds."""
        if not duration_str or not isinstance(duration_str, str):
            return 0
        try:
            parts = duration_str.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except Exception:
            pass
        return 0

    def format_time(self, seconds: float) -> str:
        """Formats seconds to MM:SS."""
        s = int(seconds)
        return f"{s // 60:02d}:{s % 60:02d}"

    def update_status(self) -> None:
        status_widget = self.query_one("#status", Static)
        time_widget = self.query_one("#time_display", Static)
        progress_bar = self.query_one(ProgressBar)
        
        if not self.player.playlist and not getattr(self, 'search_results', []):
            status_widget.update("Status: Start by searching above!")
            return

        vol_pct = int(self.player.volume * 100)
        vol_state = "MUTED" if self.player.is_muted else f"Vol: {vol_pct}%"
        modes = []
        if self.player.is_shuffled: modes.append("Shuffle")
        if self.player.is_repeating: modes.append("Repeat")
        mode_str = f"[{' | '.join(modes)}] | " if modes else ""
        mode_str = f"[MODE: {self.mode.upper()}] | " + mode_str

        song_name = self.player.get_current_song_name()
        state = "Playing" if self.player.is_playing else ("Paused" if self.player.is_paused else "Stopped")
        
        # Update progress and time
        current_song = self.player.playlist[self.player.current_index] if 0 <= self.player.current_index < len(self.player.playlist) else None
        time_str = "00:00 / 00:00"
        if current_song and (self.player.is_playing or self.player.is_paused):
            total_sec = self.parse_duration(current_song.get("duration", "0:00"))
            current_sec = self.player.get_current_pos()
            if total_sec <= 0:
                total_sec = max(1, int(current_sec) + 1)
            
            time_str = f"{self.format_time(current_sec)} / {current_song.get('duration', '0:00')}"
            time_widget.update(time_str)
            progress_bar.total = total_sec
            progress_bar.progress = current_sec
        else:
            time_widget.update(time_str)
            progress_bar.total = 100
            progress_bar.progress = 0

        results_count = len(self.search_results) if self.search_results else len(self.player.playlist)
        status = f"Query: {self.active_query} | {results_count} Results | {state} | {vol_state} | {time_str} | {mode_str}Song: {song_name}"
        status_widget.update(status)

    def check_music_end(self) -> None:
        # Also refresh progress while checking for end
        self.update_status()
        if self.player.check_finished_naturally():
            self.action_next()

if __name__ == "__main__":
    app = MusicPlayerApp()
    app.run()
