from textual.app import App, ComposeResult
from visualizer import AudioVisualizer
class TestApp(App):
    def compose(self) -> ComposeResult:
        yield AudioVisualizer()
    def on_mount(self):
        vis = self.query_one(AudioVisualizer)
        vis.is_active = True
        vis.is_playing = True
if __name__ == '__main__':
    app = TestApp()
    app.run()
