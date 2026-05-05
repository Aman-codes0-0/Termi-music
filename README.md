# 🎵 Termi-music 🎵
A lightweight, terminal-based music player that streams directly from YouTube Music with **ZERO-LAG** pre-fetching. Now supports **Linux, Windows, and Android (Termux)**.

<p align="center">
  <img src="Screenshot%202026-04-18%20031150.png" alt="Termi-music Thumbnail" width="100%">
</p>

## 🎥 Quick Start Video
Experience Termi-music in action! Watch the demo video below to see how to get started:

https://github.com/Aman-codes0-0/Termi-music/raw/main/tui_music.mp4

---

## ✨ Features
- **Cloud Streaming**: Search and play any song from YouTube Music.
- **Local Playback**: Instantly scan and play local audio files with manual folder selection.
- **Queue & Pre-Fetching**: Automatically downloads the next song while you listen, making transitions instant.
- **Auto-Cleanup**: Temporary streaming cache is deleted upon exit to save storage.
- **Modern TUI**: Built with Textual, featuring beautiful themes and keyboard-driven navigation.
- **Custom Themes**: 40+ themes available.

##  Installation

### 🐧 Linux / 🪟 Windows
1. Clone the repository:
   ```bash
   git clone https://github.com/Aman-codes0-0/Termi-music.git
   cd Termi-music
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux
   # venv\Scripts\activate   # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   python main.py
   ```
## 🎮 Controls
- `/`: Focus Search Box
- `Enter`: Search / Select Song
- `Space`: Pause / Resume
- `l`: Toggle Local / Online Mode
- `n`: Next Song
- `b`: Previous Song
- `+ / -`: Volume Up / Down
- `m`: Mute
- `s`: Toggle Shuffle
- `r`: Toggle Repeat
- `d`: Change Theme
- `Esc`: Focus Song List
- `q`: Quit
