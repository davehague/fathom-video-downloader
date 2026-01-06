#!/usr/bin/env python3
"""
Vimeo downloader for private/unlisted videos that require a signed config URL.

Usage:
    python vimeo.py "<config_url>" --output-name "Video Name" [--audio-only]

The config URL must be captured from browser DevTools:
1. Open the Vimeo video page in Chrome
2. Open Developer Tools (F12)
3. Go to Network tab
4. Play the video
5. Filter by "config" and look for XHR type requests
6. Find: player.vimeo.com/video/XXXXX/config?...
7. Right-click > Copy > Copy URL
"""

import argparse
import os
import subprocess
import sys

try:
    from curl_cffi import requests
except ImportError:
    print("Error: curl_cffi not installed. Run: pip install 'yt-dlp[curl-cffi]'")
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.expanduser("~/Movies"))


def get_hls_url(config_url: str) -> str:
    """Fetch the config URL and extract the HLS stream URL."""
    resp = requests.get(
        config_url,
        impersonate="chrome",
        headers={"Referer": "https://vimeo.com/"}
    )

    if resp.status_code != 200:
        raise Exception(f"Failed to fetch config: HTTP {resp.status_code}")

    config = resp.json()
    files = config.get("request", {}).get("files", {})

    # Try different CDN options
    hls = files.get("hls", {}).get("cdns", {})

    for cdn in ["fastly_skyfire", "akfire_interconnect_quic"]:
        if cdn in hls and "url" in hls[cdn]:
            return hls[cdn]["url"]

    raise Exception("No HLS URL found in config. Available keys: " + str(list(files.keys())))


def download_with_ffmpeg(hls_url: str, output_path: str, audio_only: bool = False):
    """Download the stream using ffmpeg."""
    if audio_only:
        cmd = [
            "ffmpeg", "-i", hls_url,
            "-vn", "-acodec", "libmp3lame", "-q:a", "0",
            output_path, "-y"
        ]
    else:
        cmd = [
            "ffmpeg", "-i", hls_url,
            "-c", "copy",
            output_path, "-y"
        ]

    print(f"Downloading to: {output_path}")
    subprocess.run(cmd, check=True)
    print(f"Done! File saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Download Vimeo videos using a signed config URL from browser DevTools"
    )
    parser.add_argument("config_url", help="The full config URL from browser DevTools")
    parser.add_argument("--output-name", "-o", required=True, help="Output filename (without extension)")
    parser.add_argument("--audio-only", "-a", action="store_true", help="Download audio only as MP3")
    parser.add_argument("--output-dir", "-d", default=OUTPUT_DIR, help=f"Output directory (default: {OUTPUT_DIR})")

    args = parser.parse_args()

    # Get the HLS URL
    print("Fetching stream URL from config...")
    hls_url = get_hls_url(args.config_url)
    print(f"Found HLS URL: {hls_url[:80]}...")

    # Build output path
    ext = "mp3" if args.audio_only else "mp4"
    output_path = os.path.join(args.output_dir, f"{args.output_name}.{ext}")

    # Download
    download_with_ffmpeg(hls_url, output_path, args.audio_only)


if __name__ == "__main__":
    main()
