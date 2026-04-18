# 🎵 Cloud TUI Music Player 🎵

A lightweight, terminal-based music player that streams directly from YouTube Music with **ZERO-LAG** pre-fetching. Now supports **Linux, Windows, and Android (Termux)**.

## ✨ Features
- **Cloud Streaming**: Search and play any song from YouTube Music.
- **Queue & Pre-Fetching**: Automatically downloads the next song while you listen, making transitions instant.
- **Universal Support**: Native drivers for Desktop (Pygame) and Android (Termux-API).
- **Modern TUI**: Built with Textual, featuring beautiful themes and keyboard-driven navigation.
- **Custom Themes**: 40+ themes available.

## 🚀 Installation

### 🐧 Linux / 🪟 Windows
1. Clone the repository:
   ```bash
   git clone https://github.com/Aman-codes0-0/tui-music-player.git
   cd tui-music-player
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

### 📱 Android (Termux)
1. Install Termux from F-Droid / Any Official Stores.
2. Install the **Termux:API** app from F-Droid and the package in Termux:
   ```bash
   pkg install termux-api ffmpeg python ndk-sysroot clang make libjpeg-turbo
   ```
3. Clone and setup:
   ```bash
   git clone https://github.com/Aman-codes0-0/tui-music-player.git
   cd tui-music-player
   pip install textual ytmusicapi yt-dlp
   ```
4. Run:
   ```bash
   python main.py
   ```

## 🎮 Controls
- `/`: Focus Search Box
- `Enter`: Search / Select Song
- `Space`: Pause / Resume
- `n`: Next Song
- `b`: Previous Song
- `+ / -`: Volume Up / Down
- `m`: Mute
- `s`: Toggle Shuffle
- `r`: Toggle Repeat
- `d`: Change Theme
- `Esc`: Focus Song List
- `q`: Quit
