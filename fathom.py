# download_from_fathom.py

import sys
import subprocess
from urllib.parse import urlparse
import os


def download_fathom_video(url):
    # Extract the ID from the URL path
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.split("/")
    # Assuming the ID is the segment before "video.m3u8"
    if len(path_segments) >= 2 and path_segments[-1] == "video.m3u8":
        video_id = path_segments[-2]
        output_filename = f"{video_id}.mp4"
    else:
        # Fallback if the URL format is unexpected
        output_filename = "output.mp4"
        print(
            f"Warning: Could not extract video ID from URL. Using default filename: {output_filename}"
        )

    print(f"Downloading video from: {url}")
    command = [
        "ffmpeg",
        "-http_persistent",
        "false",
        "-i",
        url,
        "-c",
        "copy",
        output_filename,
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Download complete: {output_filename}")
    except subprocess.CalledProcessError as e:
        print("ffmpeg failed:", e)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python download_from_fathom.py <fathom_m3u8_url>")
        sys.exit(1)

    fathom_url = sys.argv[1]
    # Append "/video.m3u8" to the URL
    fathom_url_with_m3u8 = fathom_url + "/video.m3u8"
    download_fathom_video(fathom_url_with_m3u8)
