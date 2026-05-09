# streamyard.py

import sys
import os
import re
import argparse
from urllib.parse import urlparse
import requests
from dotenv import load_dotenv


API_BASE = "https://oa-api.streamyard.com/api/public/webinars"
WATCH_BASE = "https://streamyard.com/watch"

# StreamYard's API rejects requests without this custom header as a CSRF mitigation.
# It also requires a `jwtOnAir` session cookie that gets set when you load the watch page.
API_HEADERS = {
    "x-csrf-protection": "true",
    "Origin": "https://streamyard.com",
    "Referer": "https://streamyard.com/",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def extract_webinar_id(url_or_id):
    """Accept a full StreamYard watch URL or a bare webinar ID."""
    if "/" not in url_or_id and "?" not in url_or_id:
        return url_or_id

    parsed = urlparse(url_or_id)
    parts = [p for p in parsed.path.split("/") if p]
    # Path looks like /watch/<id> or /<locale>/watch/<id>
    if "watch" in parts:
        idx = parts.index("watch")
        if idx + 1 < len(parts):
            return parts[idx + 1]

    # Fallback: last path segment
    if parts:
        return parts[-1]

    return None


def fetch_webinar_metadata(webinar_id):
    session = requests.Session()
    session.headers.update({"User-Agent": API_HEADERS["User-Agent"]})

    # Hit the watch page first so StreamYard sets the jwtOnAir session cookie
    # that the public API requires.
    try:
        warmup = session.get(f"{WATCH_BASE}/{webinar_id}", timeout=30)
        warmup.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error loading watch page to obtain session cookie: {e}")
        sys.exit(1)

    if "jwtOnAir" not in session.cookies:
        print("Failed to obtain jwtOnAir session cookie from the watch page.")
        sys.exit(1)

    try:
        response = session.get(f"{API_BASE}/{webinar_id}", headers=API_HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching webinar metadata: {e}")
        sys.exit(1)


def download_file(url, output_path):
    print(f"Downloading video from: {url[:100]}...")

    try:
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 1024 * 1024  # 1 MB

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 / total
                        mb_done = downloaded / (1024 * 1024)
                        mb_total = total / (1024 * 1024)
                        print(
                            f"Progress: {pct:5.1f}% ({mb_done:.1f}/{mb_total:.1f} MB)",
                            end="\r",
                        )
                    else:
                        mb_done = downloaded / (1024 * 1024)
                        print(f"Progress: {mb_done:.1f} MB", end="\r")

        print()
        print(f"Download complete: {output_path}")

    except requests.exceptions.RequestException as e:
        print(f"\nDownload failed: {e}")
        # Clean up partial file
        if os.path.exists(output_path):
            os.remove(output_path)
        sys.exit(1)


def sanitize_filename(name):
    # Strip characters that misbehave on macOS / common filesystems
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", name).strip()
    return cleaned or "streamyard_video"


if __name__ == "__main__":
    load_dotenv()

    parser = argparse.ArgumentParser(description="Download a StreamYard webinar recording.")
    parser.add_argument(
        "streamyard_url",
        help="A StreamYard watch URL (e.g. https://streamyard.com/watch/D3bdxzyuQKMH) or bare webinar ID.",
    )
    parser.add_argument(
        "--output-name",
        help="Optional name for the output video file (without extension). Defaults to the webinar title.",
    )
    args = parser.parse_args()

    webinar_id = extract_webinar_id(args.streamyard_url)
    if not webinar_id:
        print("Could not parse a webinar ID from the provided URL.")
        sys.exit(1)

    print(f"Fetching metadata for webinar: {webinar_id}")
    meta = fetch_webinar_metadata(webinar_id)

    title = meta.get("title") or webinar_id
    status = meta.get("status")
    vod_url = meta.get("vodUrl")

    if not meta.get("isVodEnabled", False):
        print(f"This webinar does not have VOD enabled (status: {status}). Nothing to download.")
        sys.exit(1)

    if meta.get("isVodMediaDeleted"):
        print("The recording for this webinar has been deleted by the host.")
        sys.exit(1)

    if not vod_url:
        print(
            "No vodUrl available — the webinar may still be live, processing, or require registration."
        )
        if meta.get("isRegistrationEnabled"):
            print("This webinar requires email registration before the recording can be viewed.")
        sys.exit(1)

    output_name = args.output_name or title
    output_filename = f"{sanitize_filename(output_name)}.mp4"

    output_dir = os.getenv("OUTPUT_DIR", ".")
    os.makedirs(output_dir, exist_ok=True)

    full_output_path = os.path.join(output_dir, output_filename)

    print(f'Webinar: "{title}"')
    download_file(vod_url, full_output_path)
