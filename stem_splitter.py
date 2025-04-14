#!/usr/bin/env python3
import os
import re
import json
import time
import shutil
import requests
from pathlib import Path


def get_stem_choice():
    """Ask user which stem to extract with LALAL.AI."""
    print("\nAvailable stems:")
    print("\nOrion Neural Network:")
    print("1. Vocals")
    print("2. Voice (with noise cancelling)")
    print("3. Drums")
    print("4. Piano")
    print("5. Bass")
    print("6. Electric Guitar")
    print("7. Acoustic Guitar")
    print("\nPhoenix Neural Network (higher quality):")
    print("8. Synthesizer")
    print("9. Strings")
    print("10. Wind instruments")

    while True:
        choice = input("\nEnter number of the stem to extract (1-10): ")
        try:
            choice = int(choice)
            if 1 <= choice <= 10:
                # Map choices to stem names and splitter type
                stem_map = {
                    1: ("vocals", "orion"),
                    2: ("voice", "orion"),
                    3: ("drum", "orion"),
                    4: ("piano", "orion"),
                    5: ("bass", "orion"),
                    6: ("electric_guitar", "orion"),
                    7: ("acoustic_guitar", "orion"),
                    8: ("synthesizer", "phoenix"),
                    9: ("strings", "phoenix"),
                    10: ("wind", "phoenix")
                }
                return stem_map[choice]
            else:
                print("Please enter a number between 1 and 10")
        except ValueError:
            print("Please enter a valid number")


def load_license_key():
    """
    Load LALAL.AI license key from a config file in the project directory.
    If the file doesn't exist, prompt the user for the key and save it.
    """
    # Look for the config file in the project directory
    config_file = Path(os.getcwd()) / "lalal_config.txt"
    
    # Try to load existing key
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                key = f.read().strip()
                if key and key != "YOUR_LICENSE_KEY_HERE":
                    return key
        except Exception as e:
            print(f"Error reading config file: {e}")
    
    # If we get here, we need to prompt for a key
    print("\nLALAL.AI license key not found or invalid.")
    key = input("Please enter your LALAL.AI license key: ").strip()
    
    # Save the key for future use
    try:
        with open(config_file, "w") as f:
            f.write(key)
        print(f"License key saved to {config_file}")
    except Exception as e:
        print(f"Warning: Could not save license key: {e}")
    
    return key


def validate_license_key(key):
    """Validate the LALAL.AI license key."""
    if not key or key == "YOUR_LICENSE_KEY_HERE":
        print("Error: Invalid license key")
        return False
    return True


def sanitize_filename(filename):
    """
    Sanitize a filename by removing or replacing problematic characters.
    
    Args:
        filename (str): The original filename.
        
    Returns:
        str: A sanitized filename that's safe for API use.
    """
    # Replace special Unicode characters
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    
    # Remove invalid filename characters
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    
    # Replace multiple spaces with a single space
    filename = re.sub(r'\s+', ' ', filename).strip()
    
    # Ensure filename is not empty
    if not filename:
        filename = "audio_file"
    
    return filename

def upload_file_to_lalal(file_path, license_key):
    """
    Upload a file to LALAL.AI using their API.
    
    Args:
        file_path (str): Path to the audio file.
        license_key (str): LALAL.AI license key.
        
    Returns:
        str: File ID if successful, None otherwise.
    """
    try:
        print(f"Uploading {file_path} to LALAL.AI...")
        
        # Get file name from path and sanitize it
        original_file_name = os.path.basename(file_path)
        file_name = sanitize_filename(original_file_name)
        
        print(f"Using sanitized filename: {file_name}")
        
        # Prepare the headers
        headers = {
            'Content-Disposition': f'attachment; filename={file_name}',
            'Authorization': f'license {license_key}'
        }
        
        # Open the file in binary mode and send the request
        with open(file_path, 'rb') as file_data:
            response = requests.post(
                'https://www.lalal.ai/api/upload/',
                headers=headers,
                data=file_data
            )
        
        # Parse the response
        result = response.json()
        
        if result.get('status') == 'success':
            print(f"Upload successful! File ID: {result.get('id')}")
            return result.get('id')
        else:
            print(f"Upload failed: {result.get('error')}")
            return None
            
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None


def split_file_on_lalal(file_id, stem_name, splitter_type, license_key):
    """
    Split the uploaded file on LALAL.AI.
    
    Args:
        file_id (str): The ID of the uploaded file.
        stem_name (str): The stem to extract.
        splitter_type (str): The neural network to use.
        license_key (str): LALAL.AI license key.
        
    Returns:
        str: Task ID if successful, None otherwise.
    """
    try:
        print(f"Starting stem separation for {stem_name} using {splitter_type} neural network...")
        
        # Prepare the request parameters
        params = [{
            "id": file_id,
            "stem": stem_name,
            "splitter": splitter_type
        }]
        
        # Add enhanced processing for non-voice stems
        if stem_name != "vocals" and stem_name != "voice":
            params[0]["enhanced_processing_enabled"] = True
            
        # Add noise cancelling level for voice stem
        if stem_name == "voice":
            noise_level = input("\nChoose noise cancelling level (0=mild, 1=normal, 2=aggressive) [1]: ") or "1"
            params[0]["noise_cancelling_level"] = int(noise_level)
        
        # Prepare headers
        headers = {
            'Authorization': f'license {license_key}'
        }
        
        # Make the request
        response = requests.post(
            'https://www.lalal.ai/api/split/',
            headers=headers,
            data={'params': json.dumps(params)}
        )
        
        # Parse the response
        result = response.json()
        
        if result.get('status') == 'success':
            print(f"Stem separation started successfully!")
            return result.get('task_id')
        else:
            print(f"Stem separation failed: {result.get('error')}")
            return None
            
    except Exception as e:
        print(f"Error starting stem separation: {e}")
        return None


def check_split_status(file_id, license_key):
    """
    Check the status of the split task.
    
    Args:
        file_id (str): The ID of the uploaded file.
        license_key (str): LALAL.AI license key.
        
    Returns:
        dict: Split results if successful, None otherwise.
    """
    try:
        # Prepare headers
        headers = {
            'Authorization': f'license {license_key}'
        }
        
        max_attempts = 60  # Maximum number of attempts (10 minutes)
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            
            # Make the request
            response = requests.post(
                'https://www.lalal.ai/api/check/',
                headers=headers,
                data={'id': file_id}
            )
            
            # Parse the response
            result = response.json()
            
            if result.get('status') == 'success':
                file_result = result.get('result', {}).get(file_id, {})
                
                # Check if there's a task
                task = file_result.get('task')
                if task:
                    state = task.get('state')
                    
                    if state == 'success':
                        # Split completed successfully
                        print(f"Stem separation completed successfully!")
                        return file_result.get('split')
                    elif state == 'error':
                        # Split failed
                        print(f"Stem separation failed: {task.get('error')}")
                        return None
                    elif state == 'cancelled':
                        print(f"Stem separation was cancelled.")
                        return None
                    elif state == 'progress':
                        # Still in progress, show progress and wait
                        progress = task.get('progress', 0)
                        print(f"Stem separation in progress: {progress}%")
                        time.sleep(10)  # Wait 10 seconds before checking again
                        continue
                
                # If we get here, there's no task or it's in a different state
                if file_result.get('split'):
                    # Split data already exists
                    return file_result.get('split')
                
                print(f"Waiting for stem separation to start...")
                time.sleep(10)  # Wait 10 seconds before checking again
            else:
                print(f"Error checking split status: {result.get('error')}")
                return None
                
        print("Stem separation timed out. Please check the LALAL.AI website.")
        return None
            
    except Exception as e:
        print(f"Error checking split status: {e}")
        return None


def download_split_results(split_data, processed_dir, stem_name):
    """
    Download the split results.
    
    Args:
        split_data (dict): The split data from the check_split_status function.
        processed_dir (Path): The directory to save the files to.
        stem_name (str): The stem that was extracted.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        if not split_data:
            return False
            
        # Create a timestamp to ensure unique filenames
        timestamp = int(time.time())
        
        # Download the stem track
        stem_url = split_data.get('stem_track')
        if stem_url:
            stem_file_path = processed_dir / f"{stem_name}.mp3"
            print(f"Downloading stem track to {stem_file_path}...")
            
            response = requests.get(stem_url)
            if response.status_code == 200:
                with open(stem_file_path, 'wb') as f:
                    f.write(response.content)
                print(f"Saved stem track: {stem_name}.mp3")
            else:
                print(f"Failed to download stem track: {response.status_code}")
                return False
                
        # Download the back track
        back_url = split_data.get('back_track')
        if back_url:
            back_file_path = processed_dir / f"non_{stem_name}_{timestamp}.mp3"
            print(f"Downloading backing track to {back_file_path}...")
            
            response = requests.get(back_url)
            if response.status_code == 200:
                with open(back_file_path, 'wb') as f:
                    f.write(response.content)
                print(f"Saved backing track: non_{stem_name}_{timestamp}.mp3")
            else:
                print(f"Failed to download backing track: {response.status_code}")
                return False
                
        return True
            
    except Exception as e:
        print(f"Error downloading split results: {e}")
        return False


def split_stems(audio_path):
    """
    Split an audio file into stems using LALAL.AI.
    
    Args:
        audio_path (str): Path to the audio file.
        
    Returns:
        str: Path to the directory with the processed stems, or None if splitting failed.
    """
    try:
        # Load LALAL.AI license key from config file or prompt user
        license_key = load_license_key()

        if not validate_license_key(license_key):
            return None

        # Get the base directory and file name
        audio_file = Path(audio_path)
        
        if not audio_file.exists():
            print(f"Error: File {audio_path} does not exist")
            return None
        
        # Determine the base directory structure
        # If the audio file is in a downloads/song_name/original directory
        # we want to use the 'processed' directory in the same level
        parent_dir = audio_file.parent  # This should be the 'original' directory
        
        # Check if we're in the expected directory structure
        if parent_dir.name == 'original':
            base_dir = parent_dir.parent  # This should be 'downloads/song_name'
            processed_dir = base_dir / 'processed'
        else:
            # If not in the expected structure, create a new one
            song_name = audio_file.stem
            base_dir = Path(os.getcwd()) / 'downloads' / song_name
            original_dir = base_dir / 'original'
            processed_dir = base_dir / 'processed'
            
            # Create directories
            os.makedirs(original_dir, exist_ok=True)
            os.makedirs(processed_dir, exist_ok=True)
            
            # If the audio file is not already in the original directory, copy it there
            if str(original_dir) not in str(audio_file):  # More compatible check
                new_audio_path = original_dir / audio_file.name
                shutil.copy2(audio_path, new_audio_path)
                audio_path = str(new_audio_path)
                audio_file = Path(audio_path)
        
        # Make sure the processed directory exists
        os.makedirs(processed_dir, exist_ok=True)
        
        # Get stem choice from user
        stem_name, splitter_type = get_stem_choice()
        
        # Step 1: Upload file to LALAL.AI
        file_id = upload_file_to_lalal(audio_path, license_key)
        if not file_id:
            return None
            
        # Step 2: Start the stem separation
        task_id = split_file_on_lalal(file_id, stem_name, splitter_type, license_key)
        if not task_id:
            return None
            
        # Step 3: Check the split status and wait for completion
        split_data = check_split_status(file_id, license_key)
        if not split_data:
            return None
            
        # Step 4: Download the split results
        success = download_split_results(split_data, processed_dir, stem_name)
        if not success:
            return None
            
        # Step 5: Check if we actually processed any files
        if not any(processed_dir.glob('*')):
            print("Error: No files were found or moved to the processed directory")
            return None
        
        return str(processed_dir)
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()  # Print full traceback for debugging
        return None


if __name__ == "__main__":
    import sys
    
    # Check if command-line arguments are provided
    if len(sys.argv) > 1 and sys.argv[1] == '--input':
        # We're being called with command-line arguments, but we'll ignore them
        # and process through the main function instead
        print("Command-line arguments detected but not needed for this version.")
        
    # Standard entry point for testing
    audio_path = input("Enter path to audio file: ")
    output_dir = split_stems(audio_path)
    if output_dir:
        print(f"Stems saved to: {output_dir}")
    else:
        print("Stem splitting failed.")