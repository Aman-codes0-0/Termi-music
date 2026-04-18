import random
from textual.widgets import Static
from textual.reactive import reactive

class AudioVisualizer(Static):
    """A fake audio visualizer that bounces ASCII bars when playing."""
    
    is_active = reactive(False)
    is_playing = reactive(False)
    
    def on_mount(self) -> None:
        self.bars = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        # Use a fixed number of bars covering typical span
        self.num_bars = 40
        self.current_bars = [self.bars[0]] * self.num_bars
        self.update_timer = self.set_interval(0.1, self.update_bars, pause=True)
        # Initially hidden
        self.display = False

    def watch_is_active(self, active: bool) -> None:
        self.display = active
        self._check_timer()
        if not active:
            # Hide rendering text cleanly
            self.update("")
        
    def watch_is_playing(self, playing: bool) -> None:
        self._check_timer()
        if not playing and self.is_active:
            # Reset bars to flat if stopped
            self.current_bars = [self.bars[0]] * self.num_bars
            self.update(" ".join(self.current_bars))
            
    def _check_timer(self) -> None:
        if self.is_active and self.is_playing:
            self.update_timer.resume()
        else:
            self.update_timer.pause()

    def update_bars(self) -> None:
        for i in range(self.num_bars):
            # Biased towards middle/low heights for a realistic equalizer look
            idx = int(abs(random.gauss(3, 2)))
            idx = max(0, min(len(self.bars) - 1, idx))
            self.current_bars[i] = self.bars[idx]
            
        self.update(" ".join(self.current_bars))
