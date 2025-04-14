#!/usr/bin/env python3
import os
import re
import subprocess
from urllib.parse import urlparse

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

def download_song(url):
    """
    Download a song from YouTube or SoundCloud using yt-dlp.
    
    Args:
        url (str): The URL of the YouTube or SoundCloud song.
        
    Returns:
        str: Path to the downloaded audio file, or None if download failed.
    """
    try:
        # First, get the title to create a proper directory
        title_cmd = ['yt-dlp', '--get-title', url]
        title = subprocess.check_output(title_cmd, text=True).strip()
        title = sanitize_filename(title)
        
        # Create directory structure
        base_dir = os.path.join(os.getcwd(), 'downloads', title)
        original_dir = os.path.join(base_dir, 'original')
        processed_dir = os.path.join(base_dir, 'processed')
        
        # Create directories if they don't exist
        os.makedirs(original_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)
        
        # Download the audio
        output_template = os.path.join(original_dir, '%(title)s.%(ext)s')
        cmd = [
            'yt-dlp',
            '-x',  # Extract audio
            '--audio-format', 'wav',  # Convert to WAV for best quality
            '--audio-quality', '0',  # Best quality
            '-o', output_template,
            url
        ]
        
        # Print status
        print(f"Downloading from {'SoundCloud' if is_soundcloud_url(url) else 'YouTube'}...")
        print(f"Title: {title}")
        print(f"Output directory: {original_dir}")
        
        # Run the download command
        subprocess.run(cmd, check=True)
        
        # Get the path to the downloaded file
        downloaded_file = None
        for file in os.listdir(original_dir):
            if file.endswith('.wav'):
                downloaded_file = os.path.join(original_dir, file)
                break
        
        return downloaded_file
        
    except subprocess.CalledProcessError as e:
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