# skool.py

import sys
import subprocess
import os
import re
import argparse
from dotenv import load_dotenv

HEADERS = "Referer: https://www.skool.com/\r\nUser-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\n"


def download_skool_video(m3u8_url, output_path):
    """Download video using ffmpeg from master m3u8 playlist"""
    print(f"Downloading video from Skool...")
    print(f"URL: {m3u8_url[:80]}..." if len(m3u8_url) > 80 else f"URL: {m3u8_url}")

    command = [
        "ffmpeg",
        "-headers", HEADERS,
        "-http_persistent", "false",
        "-i", m3u8_url,
        "-map", "0:v:0",  # First video stream (highest quality)
        "-map", "0:a:0",  # First audio stream
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
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

    except subprocess.CalledProcessError:
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file

    parser = argparse.ArgumentParser(
        description="Download a Skool video from m3u8 URL.",
        epilog="""
How to find the URL:
  1. Open browser DevTools (F12) > Network tab
  2. Play the video on Skool
  3. Filter by '.m3u8'
  4. Look for the master playlist from 'stream.video.skool.com' (NOT the rendition.m3u8 files)
  5. Copy the full URL including the ?token= parameter
"""
    )
    parser.add_argument(
        "m3u8_url",
        help="The master m3u8 URL from stream.video.skool.com"
    )
    parser.add_argument(
        "--output-name",
        help="Optional name for the output video file (without extension).",
    )
    args = parser.parse_args()

    m3u8_url = args.m3u8_url
    output_name = args.output_name

    # Validate URL is the master playlist, not a rendition stream
    if not m3u8_url.startswith("https://stream.video.skool.com/"):
        print("Warning: This doesn't look like the master playlist URL.")
        print("Expected: https://stream.video.skool.com/[id].m3u8?token=...")
        print()
        if "rendition.m3u8" in m3u8_url or "edgemv" in m3u8_url or "manifest-gcp" in m3u8_url:
            print("It looks like you copied a video or audio stream URL instead.")
            print("These only contain one track (video OR audio), not both.")
            print()
            print("To find the master playlist:")
            print("  1. In Network tab, filter by '.m3u8'")
            print("  2. Look for requests to 'stream.video.skool.com'")
            print("  3. It should NOT be a 'rendition.m3u8' file")
            sys.exit(1)

    # Determine the final output filename
    if output_name:
        final_output_name = output_name
    else:
        # Try to extract a meaningful name from the URL
        final_output_name = "skool_video"

        # Try to extract video ID from stream.video.skool.com URL
        # Example: /uttU8Eb8hSLv8PR8p2CoyQ02wcfOFD3byR01m5CrxYa02c.m3u8
        id_match = re.search(r'/([a-zA-Z0-9]{20,})\.m3u8', m3u8_url)
        if id_match:
            # Use first 16 chars of the ID
            final_output_name = f"skool_{id_match.group(1)[:16]}"

    output_filename = f"{final_output_name}.mp4"

    # Get output directory from environment variable, default to current directory
    output_dir = os.getenv("OUTPUT_DIR", ".")
    os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn't exist

    full_output_path = os.path.join(output_dir, output_filename)

    download_skool_video(m3u8_url, full_output_path)
