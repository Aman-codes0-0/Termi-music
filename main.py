import os
import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static, DirectoryTree, OptionList
from textual.widgets.option_list import Option
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import ModalScreen

from scanner import scan_folder, FolderNotFoundError, NoAudioFilesFoundError
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
    
    TITLE = "🎵 TUI Music Player 🎵"
    ENABLE_COMMAND_PALETTE = False
    
    CSS = """
    Screen {
        background: $surface-darken-1;
    }
    Horizontal {
        height: 1fr;
    }
    DirectoryTree {
        width: 30%;
        height: 1fr;
        margin: 1 1;
        border: round $secondary;
        background: $surface;
    }
    DataTable {
        width: 70%;
        height: 1fr;
        margin: 1 2 1 0;
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
        Binding("d", "select_theme", "Themes", priority=True),
        Binding("q", "quit", "Quit", priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield DirectoryTree(os.path.expanduser("~"), id="directory_tree")
            yield DataTable(id="song_list")
        yield Static("Status: Select a folder from the tree on the left", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.theme = load_theme()
        self.player = MusicPlayer()
        self.active_folder = ""
        
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("ID", "Song Name")
        
        self.set_interval(1.0, self.check_music_end)
        
    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.load_folder(str(event.path))
        
    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.load_folder(str(event.path.parent))
        
    def load_folder(self, folder_path: str) -> None:
        try:
            songs = scan_folder(folder_path)
            self.active_folder = folder_path
            self.player.load_playlist(songs)
            
            table = self.query_one(DataTable)
            table.clear()
            for idx, song in enumerate(songs):
                table.add_row(str(idx + 1), os.path.basename(song))
                
            self.notify(f"Successfully loaded {len(songs)} tracks!", title="Scanning Complete")
            self.update_status()
            
        except FolderNotFoundError as e:
            self.notify(str(e), title="Path Error", severity="error")
        except NoAudioFilesFoundError:
            self.notify(f"No files found in {os.path.basename(folder_path)}", title="No Audio", severity="warning")

    def watch_player_index(self) -> None:
        if self.player.current_index != -1 and self.player.playlist:
            table = self.query_one(DataTable)
            table.move_cursor(row=self.player.current_index)
            
    def action_play(self) -> None:
        if not self.player.is_playing and not self.player.is_paused:
            table = self.query_one(DataTable)
            if table.cursor_row is not None and self.player.playlist:
                self.player.play(table.cursor_row)
            else:
                return
        self.update_status()

    def action_toggle_pause(self) -> None:
        self.player.toggle_pause()
        self.update_status()

    def action_next(self) -> None:
        self.player.next()
        self.watch_player_index()
        self.update_status()

    def action_previous(self) -> None:
        self.player.previous()
        self.watch_player_index()
        self.update_status()

    def action_select_theme(self) -> None:
        self.push_screen(ThemeSelector())

    def action_quit(self) -> None:
        self.player.quit()
        self.exit()

    def update_status(self) -> None:
        status_widget = self.query_one("#status", Static)
        if not self.player.playlist:
            status_widget.update("Status: Select a folder from the tree on the left")
            return

        song_name = self.player.get_current_song_name()
        state = "Playing" if self.player.is_playing else ("Paused" if self.player.is_paused else "Stopped")
        status = f"Folder: {os.path.basename(self.active_folder)} | Total: {len(self.player.playlist)} | {state} | Song: {song_name}"
        status_widget.update(status)

    def check_music_end(self) -> None:
        if self.player.check_finished_naturally():
            self.action_next()
            
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.player.stop()
        self.player.play(event.cursor_row)
        self.update_status()

if __name__ == "__main__":
    app = MusicPlayerApp()
    app.run()
