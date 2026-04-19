# 🎵 Termi-music 🎵

A lightweight, terminal-based music player that streams directly from YouTube Music with **ZERO-LAG** pre-fetching. Now supports **Linux, Windows, and Android (Termux)**.

![Termi-music Screenshot](screenshot.png)

## ✨ Features
- **Cloud Streaming**: Search and play any song from YouTube Music.
- **Local Playback**: Instantly scan and play local audio files with manual folder selection.
- **Queue & Pre-Fetching**: Automatically downloads the next song while you listen, making transitions instant.
- **Auto-Cleanup**: Temporary streaming cache is deleted upon exit to save storage.
- **Modern TUI**: Built with Textual, featuring beautiful themes and keyboard-driven navigation.
- **Custom Themes**: 40+ themes available.

## 💻 System Requirements
This application is extremely lightweight and terminal-based, designed to run smoothly even on older or low-end hardware.

- **RAM**: ~40-60 MB at idle. Peaks around 80-150 MB during `yt-dlp` online audio extraction. (512 MB to 1 GB total system RAM is more than enough).
- **CPU**: Minimal usage. Any standard processor from the last 10-15 years is fully capable of rendering the TUI and decoding audio without lag.
- **Storage**: ~50-100 MB for the app and its Python dependencies. Cached online songs are automatically deleted when the app closes, ensuring your storage space remains free.
- **Software**: Python 3.8+ and `ffmpeg` (required for extracting audio from YouTube streams).

## 🚀 Installation

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

### 📱 Android (Termux)
1. Install Termux from F-Droid / Any Official Stores.
2. Install the **Termux:API** app from F-Droid and the package in Termux:
   ```bash
   pkg install termux-api ffmpeg python ndk-sysroot clang make libjpeg-turbo
   ```
3. Clone and setup:
   ```bash
   git clone https://github.com/Aman-codes0-0/Termi-music.git
   cd Termi-music
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

## 🔨 Build from Source (Standalone Binary)
If you want to create a standalone executable that doesn't require Python:
1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Run the build command:
   ```bash
   pyinstaller --onefile --name "Termi-music" --clean main.py
   ```
3. The binary will be available in the `dist/` folder.
