# mike-audio-tools

A Python application for audio processing tasks like downloading songs from YouTube/SoundCloud and splitting them into stems using LALAL.AI.

## Features

- Download songs from YouTube or SoundCloud
- Split audio files into stems using LALAL.AI's neural networks
- Combined workflow to download and then split songs
- Organized file structure for projects
- Support for multiple stem types:
  - Vocals
  - Voice (with noise cancelling)
  - Drums
  - Piano
  - Bass
  - Electric Guitar
  - Acoustic Guitar
  - Synthesizer
  - Strings
  - Wind instruments

## Installation

1. Clone this repository or download the files

2. Create a virtual environment and activate it:

```bash
# Create the virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## LALAL.AI License Key

This tool uses LALAL.AI's API for stem separation. You need to have a valid LALAL.AI license key to use the stem separation features. 

When you first run the application and attempt to split stems, you'll be prompted to enter your license key. The key will be saved to a local file (`lalal_config.txt`) so you don't need to enter it again.

To obtain a LALAL.AI license key:
1. Create an account on [LALAL.AI](https://www.lalal.ai/)
2. Purchase a subscription or credits
3. Find your license key in your account settings

## Usage

Run the main application:

```bash
python main.py
```

This will display the main menu with the following options:

1. **Download song from YouTube/SoundCloud** - Download a song by providing a URL
2. **Split song into stems** - Split an existing audio file into stems
3. **Download and split song** - Combine both operations
0. **Exit** - Exit the application

### Stem Separation Options

When splitting a song, you can choose from the following stem types:

**Orion Neural Network:**
1. Vocals
2. Voice (with noise cancelling)
3. Drums
4. Piano
5. Bass
6. Electric Guitar
7. Acoustic Guitar

**Phoenix Neural Network (higher quality):**
8. Synthesizer
9. Strings
10. Wind instruments

## File Structure

When you download and process a song, the app creates the following structure:

```
downloads/
└── Song Name/
    ├── original/
    │   └── Song Name.wav
    └── processed/
        ├── piano.mp3
        ├── non_piano_1681234567.mp3
        ├── vocals.mp3
        └── non_vocals_1681234570.mp3
```

The `non_*` files are the backing tracks (original song minus the extracted stem).

## Modules

- `main.py` - Main application with menu interface
- `downloader.py` - Handles downloading songs from YouTube/SoundCloud
- `stem_splitter.py` - Handles splitting audio into stems using LALAL.AI

## Requirements

- Python 3.7+
- yt-dlp
- colorama
- requests
- FFmpeg (for downloading from YouTube/SoundCloud)

## Troubleshooting

- If you encounter issues with the LALAL.AI API, check that your license key is valid and that you have sufficient credits.
- For YouTube download issues, make sure yt-dlp is up-to-date: `pip install -U yt-dlp`
- If you're seeing "Upload failed" messages, check your internet connection and file size (LALAL.AI has a 2GB limit with license).
- For other issues, check the console output for detailed error messages.
