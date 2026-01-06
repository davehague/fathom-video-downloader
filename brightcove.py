# brightcove.py

import sys
import subprocess
import os
import re
import argparse
from dotenv import load_dotenv


def download_brightcove_video(m3u8_url, output_path):
    """Download video using ffmpeg"""
    print(f"Downloading video from Brightcove...")
    print(f"URL: {m3u8_url[:80]}..." if len(m3u8_url) > 80 else f"URL: {m3u8_url}")

    command = [
        "ffmpeg",
        "-http_persistent",
        "false",
        "-i",
        m3u8_url,
        "-c",
        "copy",
        "-bsf:a",
        "aac_adtstoasc",
        output_path,
    ]

    try:
        # Use subprocess.Popen to capture stderr in real-time
        process = subprocess.Popen(
            command, stderr=subprocess.PIPE, universal_newlines=True
        )

        # Simple progress tracking based on time
        time_pattern = re.compile(r'time=(\d{2}:\d{2}:\d{2}\.\d{2})')
        error_lines = []

        while True:
            output = process.stderr.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                # Collect error lines for better error reporting
                if "error" in output.lower() or "HTTP error" in output:
                    error_lines.append(output.strip())

                time_match = time_pattern.search(output)
                if time_match:
                    print(f"Progress: {time_match.group(1)}", end="\r")

        print()  # New line after progress

        if process.returncode != 0:
            if error_lines:
                print("\nffmpeg errors:")
                for line in error_lines[-5:]:  # Show last 5 error lines
                    print(f"  {line}")

            # Check for common errors
            if any("HTTP error 40" in line for line in error_lines):
                print("\nThe m3u8 URL appears to be expired or invalid.")
                print("Try getting a fresh URL from the browser's Network tab.")

            raise subprocess.CalledProcessError(process.returncode, command)

        print(f"Download complete: {output_path}")

    except subprocess.CalledProcessError as e:
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file

    parser = argparse.ArgumentParser(
        description="Download a Brightcove video from m3u8 URL.",
        epilog="Note: The m3u8 URL (including fastly_token) can be found in browser DevTools > Network tab. Look for master.m3u8 files."
    )
    parser.add_argument(
        "m3u8_url",
        help="The full m3u8 URL from Network tab (including all query parameters like fastly_token)."
    )
    parser.add_argument(
        "--output-name",
        help="Optional name for the output video file (without extension).",
    )
    args = parser.parse_args()

    m3u8_url = args.m3u8_url
    output_name = args.output_name

    # Determine the final output filename
    if output_name:
        final_output_name = output_name
    else:
        # Try to extract a meaningful name from the URL
        # Look for patterns in Brightcove URLs
        final_output_name = "brightcove_video"

        # Try to extract video ID or other identifiers
        id_match = re.search(r'/([a-zA-Z0-9_-]{10,})/', m3u8_url)
        if id_match:
            final_output_name = f"brightcove_{id_match.group(1)[:12]}"

    output_filename = f"{final_output_name}.mp4"

    # Get output directory from environment variable, default to current directory
    output_dir = os.getenv("OUTPUT_DIR", ".")
    os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn't exist

    full_output_path = os.path.join(output_dir, output_filename)

    download_brightcove_video(m3u8_url, full_output_path)
