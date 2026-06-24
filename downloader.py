#!/usr/bin/env python3
import os
import re
import shutil
from urllib.parse import urlparse

import yt_dlp


def sanitize_filename(name):
    """Sanitize a filename by removing invalid characters."""
    # Remove invalid filename characters
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    # Replace multiple spaces with a single space
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def is_soundcloud_url(url):
    """Check if the URL is from SoundCloud."""
    parsed_url = urlparse(url)
    return parsed_url.netloc == 'soundcloud.com' or parsed_url.netloc.endswith('.soundcloud.com')

def is_youtube_url(url):
    """Check if the URL is from YouTube."""
    parsed_url = urlparse(url)
    return (parsed_url.netloc == 'youtube.com' or 
            parsed_url.netloc == 'www.youtube.com' or 
            parsed_url.netloc == 'youtu.be')

def get_js_runtimes():
    """
    Return available JavaScript runtimes for YouTube challenge solving.
    yt-dlp requires a JS runtime to decrypt YouTube stream signatures.
    """
    runtimes = {}
    for runtime, command in [('deno', 'deno'), ('node', 'node'), ('quickjs', 'qjs')]:
        if shutil.which(command):
            runtimes[runtime] = {}
    return runtimes

def _build_ydl_opts(output_template, for_youtube=False):
    """Build yt-dlp options for audio extraction."""
    opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '0',
        }],
    }
    if for_youtube:
        js_runtimes = get_js_runtimes()
        if js_runtimes:
            opts['js_runtimes'] = js_runtimes
    return opts

def download_song(url):
    """
    Download a song from YouTube or SoundCloud using yt-dlp.
    
    Args:
        url (str): The URL of the YouTube or SoundCloud song.
        
    Returns:
        str: Path to the downloaded audio file, or None if download failed.
    """
    try:
        for_youtube = is_youtube_url(url)

        if for_youtube and not get_js_runtimes():
            print("ERROR: YouTube downloads require a JavaScript runtime (deno or node).")
            print("Install Node.js (https://nodejs.org/) or Deno (https://deno.com/).")
            return None

        info_opts = _build_ydl_opts('%(title)s.%(ext)s', for_youtube=for_youtube)
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        title = sanitize_filename(info.get('title', 'untitled'))

        # Create directory structure
        base_dir = os.path.join(os.getcwd(), 'downloads', title)
        original_dir = os.path.join(base_dir, 'original')
        processed_dir = os.path.join(base_dir, 'processed')

        # Create directories if they don't exist
        os.makedirs(original_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)

        output_template = os.path.join(original_dir, '%(title)s.%(ext)s')
        ydl_opts = _build_ydl_opts(output_template, for_youtube=for_youtube)

        # Print status
        print(f"Downloading from {'SoundCloud' if is_soundcloud_url(url) else 'YouTube'}...")
        print(f"Title: {title}")
        print(f"Output directory: {original_dir}")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Get the path to the downloaded file
        downloaded_file = None
        for file in os.listdir(original_dir):
            if file.endswith('.wav'):
                downloaded_file = os.path.join(original_dir, file)
                break

        return downloaded_file

    except yt_dlp.utils.DownloadError as e:
        print(f"Error downloading song: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

if __name__ == "__main__":
    # Test the module
    url = input("Enter YouTube or SoundCloud URL: ")
    output_path = download_song(url)
    if output_path:
        print(f"Downloaded to: {output_path}")
    else:
        print("Download failed.")
