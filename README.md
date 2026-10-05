# Video Downloaders

This repository contains scripts for downloading videos from various platforms:
- `fathom.py` - Downloads videos from Fathom
- `boxcast.py` - Downloads videos from BoxCast
- `vimeo.py` - Downloads private/unlisted Vimeo videos that require authentication
- `streamyard.py` - Downloads recordings of public StreamYard webinars

All scripts use ffmpeg and provide progress indicators during download.

## Prerequisites

- Python 3.6 or higher
- ffmpeg installed and available in your system's PATH.
- `requests` and `python-dotenv` Python packages. You can install them using pip:
  ```bash
  pip install requests python-dotenv
  ```
- For Vimeo downloads, `curl_cffi` is also required:
  ```bash
  pip install 'yt-dlp[curl-cffi]'
  ```

## Installation

It is recommended to use a virtual environment to manage the project's dependencies.

1.  **Clone the repository or download the script:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
    (Replace `<repository_url>` and `<repository_directory>` with the actual details if this script is part of a repository)

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**

    -   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```
    -   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```

4.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Create a `.env` file (Optional):**
    If you want to specify a default output directory for your downloaded videos, create a file named `.env` in the same directory as the script and add the following line:
    ```dotenv
    OUTPUT_DIR=/path/to/your/output/directory
    ```
    Replace `/path/to/your/output/directory` with the desired path. If the `OUTPUT_DIR` is not specified in the `.env` file, the script will save the video in the current directory.

### Fathom Videos

2.  **Run the Fathom script:**

    ```bash
    python fathom.py <fathom_base_url> [--output-name <video_name>]
    ```

    -   `<fathom_base_url>`: The base URL of the Fathom video (e.g., `https://fathom.video/share/z9R_xcgWVJhQsfQEagyA3toiGbeUtuHj`). The script will automatically append `/video.m3u8` to this URL.
    -   `--output-name <video_name>` (Optional): Specify a custom name for the output video file (without the `.mp4` extension). If not provided, the script will use the video ID extracted from the URL as the filename.

    **Example:**

    ```bash
    python fathom.py https://fathom.video/share/z9R_xcgWVJhQsfQEagyA3toiGbeUtuHj --output-name "AMA with Chris"
    ```

    This will download the video and save it as `AMA with Chris.mp4` in the specified `OUTPUT_DIR` (or the current directory if `OUTPUT_DIR` is not set).

### BoxCast Videos

**City of Worthington meetings, by date (no dev tools needed):**

```bash
python boxcast.py --body arb --date 2026-09-24 --output-name "2026-09-24 Worthington ARB MPC"
```

`--body` is `council`, `arb` or `bza`. `--height` picks the rendition (default 720; 240, 480, 720 and 1080 exist). The script looks the meeting up through the same unauthenticated endpoints the embedded player uses. If the city has not yet trimmed the pre-meeting lead-in off the recording it says so; the download is then the full recording and its timestamps will run later than the posted video.

**Any other BoxCast video, by URL:**

3.  **Get the m3u8 URL from BoxCast:**
    
    BoxCast videos require you to extract the m3u8 URL manually due to expiring signed URLs:
    
    1. Open the BoxCast page in Chrome
    2. Open Chrome Developer Tools (F12)
    3. Go to the Network tab
    4. Click play on the video
    5. Filter by "m3u8" in the Network tab
    6. Look for URLs containing `240p-byteranges.m3u8` (recommended for faster downloads)
    7. Copy the full URL including all parameters

4.  **Run the BoxCast script:**

    ```bash
    python boxcast.py "<m3u8_url>" [--output-name <video_name>]
    ```

    **Example:**

    ```bash
    python boxcast.py "https://play.boxcast.com/p/zvvyzetbuprcu7anat5a/r/361.259s/8876.08s/v/240p-byteranges.m3u8?Expires=1753315200&Signature=..." --output-name "2025-07-14 City Council"
    ```

    **Note:** BoxCast URLs expire quickly, so you'll need to get a fresh URL each time. The 240p version downloads much faster and is sufficient quality for most meeting videos.

### Vimeo Videos

Vimeo videos that are private or unlisted (URLs like `vimeo.com/123456/abc123`) often fail with yt-dlp showing "The web client only works when logged-in". This script works around that by using the signed config URL from your browser.

5.  **Get the config URL from Vimeo:**

    1. Open the Vimeo video page in Chrome
    2. Open Chrome Developer Tools (F12 or Cmd+Option+I)
    3. Go to the Network tab
    4. Click play on the video
    5. Filter by "config"
    6. Look for a request with **Type: xhr** to `player.vimeo.com/video/XXXXX/config?...`
    7. Right-click > Copy > Copy URL
    8. The URL will have a `&s=` signature parameter at the end

6.  **Run the Vimeo script:**

    ```bash
    python vimeo.py "<config_url>" --output-name "<video_name>" [--audio-only]
    ```

    **Examples:**

    Download as video (MP4):
    ```bash
    python vimeo.py "https://player.vimeo.com/video/835563352/config?h=abc123&...&s=signature" --output-name "My Video"
    ```

    Download as audio only (MP3):
    ```bash
    python vimeo.py "https://player.vimeo.com/video/835563352/config?h=abc123&...&s=signature" --output-name "My Audio" --audio-only
    ```

    **Note:** Config URLs contain a signature that expires, so you'll need to get a fresh URL each time.

### StreamYard Videos

StreamYard publishes webinar recordings as direct signed MP4s. The script just needs the public watch URL — no DevTools work required.

7.  **Run the StreamYard script:**

    ```bash
    python streamyard.py "<streamyard_watch_url>" [--output-name <video_name>]
    ```

    -   `<streamyard_watch_url>`: A StreamYard watch URL (e.g., `https://streamyard.com/watch/D3bdxzyuQKMH`). Bare webinar IDs are also accepted. Query parameters are ignored.
    -   `--output-name <video_name>` (Optional): Custom name for the output file (without extension). Defaults to the webinar's title.

    **Example:**

    ```bash
    python streamyard.py "https://streamyard.com/watch/D3bdxzyuQKMH" --output-name "Q&A Ideabrowser"
    ```

    **Notes:**
    -   Only works for webinars where the host has VOD (recording playback) enabled and hasn't deleted the media.
    -   Webinars that require email registration are not currently supported — the script will tell you if it hits one.

## How it works

### Fathom Script (`fathom.py`)

1.  Loads environment variables from the `.env` file.
2.  Parses command-line arguments using `argparse`.
3.  Constructs the full m3u8 URL by appending `/video.m3u8`.
4.  Fetches the content of the m3u8 playlist file.
5.  Parses the m3u8 content to get a list of video chunk URLs and counts the total number of chunks.
6.  Uses `ffmpeg` to download the video with progress tracking based on chunk count.

### BoxCast Script (`boxcast.py`)

1.  Loads environment variables from the `.env` file.
2.  Parses command-line arguments using `argparse`.
3.  Detects if the URL is already an m3u8 URL or a BoxCast embed page.
4.  For embed pages, attempts to extract the m3u8 URL from the page content.
5.  For direct m3u8 URLs, uses them directly.
6.  Uses `ffmpeg` to download the video with progress tracking based on time elapsed.
7.  Provides better error messages for expired URLs.

### Vimeo Script (`vimeo.py`)

1.  Loads environment variables from the `.env` file.
2.  Parses command-line arguments using `argparse`.
3.  Fetches the signed config URL using `curl_cffi` with browser impersonation.
4.  Extracts the HLS stream URL from the config JSON response.
5.  Uses `ffmpeg` to download the video or audio from the HLS stream.
6.  Supports audio-only downloads (converts to MP3).

### StreamYard Script (`streamyard.py`)

1.  Loads environment variables from the `.env` file.
2.  Parses the webinar ID out of the provided watch URL.
3.  Loads the watch page once to obtain a `jwtOnAir` session cookie that StreamYard's public API requires.
4.  Calls `https://oa-api.streamyard.com/api/public/webinars/{id}` (with the `x-csrf-protection: true` header) to retrieve the webinar metadata, including a signed `vodUrl`.
5.  Streams the MP4 directly to disk with a progress indicator. No `ffmpeg` involved.

All scripts:
- Determine the output filename based on the provided `--output-name` or extract an ID from the URL.
- Use the `OUTPUT_DIR` environment variable or current directory for output location.
- Create the output directory if it doesn't exist.
- Display progress indicators during download.
- Report completion or errors encountered during the process.