#!/usr/bin/env python3
import os
import re
import time
import shutil
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import quote, unquote

import requests

API_BASE = "https://www.lalal.ai/api/v1/"

# Stems supported by the multistem endpoint (max 6 per request).
MULTISTEM_STEMS = [
    "vocals",
    "drum",
    "piano",
    "bass",
    "electric_guitar",
    "acoustic_guitar",
]

# Phoenix-only stems (must be requested individually).
PHOENIX_STEMS = ["synthesizer", "strings", "wind"]

STEM_CHOICES = [
    ("Vocal and Instrumental", "vocals", "stem_separator"),
    ("Drums", "drum", "stem_separator"),
    ("Bass", "bass", "stem_separator"),
    ("Voice and Noise", "voice", "voice_clean"),
    ("Electric guitar", "electric_guitar", "stem_separator"),
    ("Acoustic guitar", "acoustic_guitar", "stem_separator"),
    ("Piano", "piano", "stem_separator"),
    ("Synthesizer", "synthesizer", "stem_separator"),
    ("Strings", "strings", "stem_separator"),
    ("Wind", "wind", "stem_separator"),
]


def get_stem_choice():
    """Ask user which stem to extract with LALAL.AI."""
    print("\nAvailable stems:")
    for index, (label, _, _) in enumerate(STEM_CHOICES, start=1):
        print(f"{index}. {label}")
    print(f"{len(STEM_CHOICES) + 1}. Export all stems")
    print(f"{len(STEM_CHOICES) + 2}. Multistem only (vocals, drums, piano, bass, guitars)")

    export_all_choice = len(STEM_CHOICES) + 1
    multistem_choice = len(STEM_CHOICES) + 2
    while True:
        choice = input(f"\nEnter number of the stem to extract (1-{multistem_choice}): ")
        try:
            choice = int(choice)
            if choice == export_all_choice:
                return None, "export_all"
            if choice == multistem_choice:
                return None, "multistem"
            if 1 <= choice <= len(STEM_CHOICES):
                label, stem_name, endpoint = STEM_CHOICES[choice - 1]
                print(f"Selected: {label}")
                return stem_name, endpoint
            print(f"Please enter a number between 1 and {multistem_choice}")
        except ValueError:
            print("Please enter a valid number")


def load_license_key():
    """
    Load LALAL.AI license key from a config file in the project directory.
    If the file doesn't exist, prompt the user for the key and save it.
    """
    config_file = Path(os.getcwd()) / "lalal_config.txt"

    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                key = f.read().strip()
                if key and key != "YOUR_LICENSE_KEY_HERE":
                    return key
        except Exception as e:
            print(f"Error reading config file: {e}")

    print("\nLALAL.AI license key not found or invalid.")
    key = input("Please enter your LALAL.AI license key: ").strip()

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
    """Sanitize a filename by removing or replacing problematic characters."""
    filename = filename.encode("ascii", "ignore").decode("ascii")
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    filename = re.sub(r"\s+", " ", filename).strip()
    return filename or "audio_file"


def _headers(license_key):
    return {"X-License-Key": license_key}


def _make_content_disposition(filename, disposition="attachment"):
    try:
        filename.encode("ascii")
        file_expr = f'filename="{filename}"'
    except UnicodeEncodeError:
        file_expr = f"filename*=utf-8''{quote(filename)}"
    return f"{disposition}; {file_expr}"


def _api_request(method, endpoint, license_key, **kwargs):
    """Make an API request and raise on HTTP errors."""
    url = API_BASE + endpoint
    headers = _headers(license_key)
    if "headers" in kwargs:
        headers.update(kwargs.pop("headers"))

    response = requests.request(method, url, headers=headers, timeout=kwargs.pop("timeout", 30), **kwargs)
    if response.status_code != 200:
        raise RuntimeError(f"API request failed ({response.status_code}): {response.text}")
    return response.json()


def upload_file_to_lalal(file_path, license_key):
    """Upload a file to LALAL.AI and return the source_id."""
    try:
        print(f"Uploading {file_path} to LALAL.AI...")

        original_file_name = os.path.basename(file_path)
        file_name = sanitize_filename(original_file_name)
        print(f"Using sanitized filename: {file_name}")

        headers = {
            "Content-Disposition": _make_content_disposition(file_name),
            **_headers(license_key),
        }

        with open(file_path, "rb") as file_data:
            response = requests.post(
                API_BASE + "upload/",
                headers=headers,
                data=file_data,
                timeout=120,
            )

        if response.status_code != 200:
            print(f"Upload failed ({response.status_code}): {response.text}")
            return None

        result = response.json()
        source_id = result.get("id")
        if not source_id:
            print("Upload failed: no source ID returned")
            return None

        print(f"Upload successful! Source ID: {source_id}")
        return source_id

    except Exception as e:
        print(f"Error uploading file: {e}")
        return None


def _splitter_for_stem(stem_name):
    if stem_name in PHOENIX_STEMS:
        return "phoenix"
    return "auto"


def _prompt_noise_cancelling_level():
    while True:
        noise_level = input("\nChoose noise cancelling level (0=mild, 1=normal, 2=aggressive) [1]: ") or "1"
        if noise_level in {"0", "1", "2"}:
            return int(noise_level)
        print("Please enter 0, 1, or 2")


def start_stem_separator_task(source_id, stem_name, license_key, splitter=None, extraction_level="deep_extraction"):
    """Start a single stem separation task and return the task_id."""
    presets = {
        "stem": stem_name,
        "splitter": splitter or _splitter_for_stem(stem_name),
        "extraction_level": extraction_level,
    }
    body = {"source_id": source_id, "presets": presets}
    result = _api_request("POST", "split/stem_separator/", license_key, json=body)
    return result["task_id"]


def start_voice_clean_task(source_id, license_key, noise_cancelling_level=1):
    """Start a voice cleaning task and return the task_id."""
    presets = {
        "stem": "voice",
        "noise_cancelling_level": noise_cancelling_level,
        "splitter": "auto",
    }
    body = {"source_id": source_id, "presets": presets}
    result = _api_request("POST", "split/voice_clean/", license_key, json=body)
    return result["task_id"]


def start_multistem_task(source_id, license_key, extraction_level="deep_extraction"):
    """Start a multistem separation task and return the task_id."""
    presets = {
        "stem_list": MULTISTEM_STEMS,
        "splitter": "auto",
        "extraction_level": extraction_level,
    }
    body = {"source_id": source_id, "presets": presets}
    result = _api_request("POST", "split/multistem/", license_key, json=body)
    return result["task_id"]


def start_export_all_tasks(source_id, license_key, noise_cancelling_level=1):
    """Start all tasks needed to export every stem type."""
    task_ids = []

    print("Starting multistem separation (vocals, drums, piano, bass, guitars)...")
    task_ids.append(start_multistem_task(source_id, license_key))

    for stem_name in PHOENIX_STEMS:
        print(f"Starting {stem_name} separation (Phoenix)...")
        task_ids.append(start_stem_separator_task(source_id, stem_name, license_key, splitter="phoenix"))

    print("Starting voice and noise separation...")
    task_ids.append(start_voice_clean_task(source_id, license_key, noise_cancelling_level))

    return task_ids


def start_split_task(source_id, stem_name, endpoint, license_key):
    """Start a single split task based on the selected stem type."""
    if endpoint == "export_all":
        noise_level = _prompt_noise_cancelling_level()
        return start_export_all_tasks(source_id, license_key, noise_level)

    if endpoint == "multistem":
        print("Starting multistem separation (vocals, drums, piano, bass, guitars)...")
        return [start_multistem_task(source_id, license_key)]

    if endpoint == "voice_clean":
        noise_level = _prompt_noise_cancelling_level()
        print(f"Starting voice separation with noise cancelling level {noise_level}...")
        return [start_voice_clean_task(source_id, license_key, noise_level)]

    print(f"Starting {stem_name} separation...")
    return [start_stem_separator_task(source_id, stem_name, license_key)]


def wait_for_tasks(task_ids, license_key):
    """Poll task status until all tasks complete and return their results."""
    pending = set(task_ids)
    completed_results = {}
    max_attempts = 120
    attempt = 0

    while pending and attempt < max_attempts:
        attempt += 1
        try:
            check_result = _api_request(
                "POST",
                "check/",
                license_key,
                json={"task_ids": list(pending)},
            )
        except RuntimeError as e:
            print(f"Error checking split status: {e}")
            return None

        results = check_result.get("result", {})
        for task_id in list(pending):
            task_status = results.get(task_id)
            if not task_status:
                continue

            status = task_status.get("status")
            if status == "success":
                print(f"Task {task_id[:8]}... completed.")
                completed_results[task_id] = task_status["result"]
                pending.remove(task_id)
            elif status == "error":
                error = task_status.get("error", {})
                detail = error.get("detail") if isinstance(error, dict) else error
                print(f"Task {task_id[:8]}... failed: {detail}")
                return None
            elif status == "cancelled":
                print(f"Task {task_id[:8]}... was cancelled.")
                return None
            elif status == "server_error":
                print(f"Task {task_id[:8]}... server error: {task_status.get('error')}")
                return None
            elif status == "progress":
                progress = task_status.get("progress", 0)
                if progress:
                    print(f"Task {task_id[:8]}... progress: {progress}%")
                elif attempt == 1:
                    print(f"Task {task_id[:8]}... queued.")

        if pending:
            time.sleep(5)

    if pending:
        print("Stem separation timed out. Please check the LALAL.AI website.")
        return None

    return completed_results


def _filename_from_content_disposition(header):
    msg = EmailMessage()
    msg["content-disposition"] = header
    filename = msg.get_filename()
    if filename:
        return filename

    if header and "filename*=" in header:
        for raw_segment in header.split(";"):
            segment = raw_segment.strip()
            if segment.startswith("filename*="):
                encoded = segment.split("=", 1)[1]
                if "''" in encoded:
                    encoding, quoted = encoded.split("''", 1)
                    return unquote(quoted, encoding)

    return None


def _download_track(url, processed_dir, fallback_name):
    response = requests.get(url, stream=True, timeout=120)
    if response.status_code != 200:
        print(f"Failed to download {fallback_name}: HTTP {response.status_code}")
        return False

    filename = _filename_from_content_disposition(response.headers.get("Content-Disposition", ""))
    if not filename:
        filename = f"{fallback_name}.mp3"

    filename = sanitize_filename(filename)
    file_path = processed_dir / filename

    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print(f"Saved: {file_path.name}")
    return True


def download_split_results(split_results, processed_dir):
    """Download all tracks from one or more completed split results."""
    if not split_results:
        return False

    success = True
    for result in split_results.values():
        for track in result.get("tracks", []):
            label = track.get("label", "track")
            track_type = track.get("type", "stem")
            url = track.get("url")
            if not url:
                continue

            fallback_name = label if track_type == "stem" else f"no_{label}"
            if not _download_track(url, processed_dir, fallback_name):
                success = False

    return success


def _resolve_output_dirs(audio_path):
    """Resolve the processed output directory for an audio file."""
    audio_file = Path(audio_path)
    parent_dir = audio_file.parent

    if parent_dir.name == "original":
        base_dir = parent_dir.parent
        processed_dir = base_dir / "processed"
    else:
        song_name = audio_file.stem
        base_dir = Path(os.getcwd()) / "downloads" / song_name
        original_dir = base_dir / "original"
        processed_dir = base_dir / "processed"
        os.makedirs(original_dir, exist_ok=True)

        if str(original_dir) not in str(audio_file):
            new_audio_path = original_dir / audio_file.name
            shutil.copy2(audio_path, new_audio_path)
            audio_path = str(new_audio_path)

    os.makedirs(processed_dir, exist_ok=True)
    return audio_path, processed_dir


def split_stems(audio_path):
    """
    Split an audio file into stems using LALAL.AI API v1.

    Args:
        audio_path (str): Path to the audio file.

    Returns:
        str: Path to the directory with the processed stems, or None if splitting failed.
    """
    try:
        license_key = load_license_key()
        if not validate_license_key(license_key):
            return None

        audio_file = Path(audio_path)
        if not audio_file.exists():
            print(f"Error: File {audio_path} does not exist")
            return None

        audio_path, processed_dir = _resolve_output_dirs(audio_path)
        stem_name, endpoint = get_stem_choice()

        source_id = upload_file_to_lalal(file_path=audio_path, license_key=license_key)
        if not source_id:
            return None

        task_ids = start_split_task(source_id, stem_name, endpoint, license_key)
        if not task_ids:
            return None

        split_results = wait_for_tasks(task_ids, license_key)
        if not split_results:
            return None

        if not download_split_results(split_results, processed_dir):
            return None

        if not any(processed_dir.glob("*")):
            print("Error: No files were found in the processed directory")
            return None

        return str(processed_dir)

    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    audio_path = input("Enter path to audio file: ")
    output_dir = split_stems(audio_path)
    if output_dir:
        print(f"Stems saved to: {output_dir}")
    else:
        print("Stem splitting failed.")
