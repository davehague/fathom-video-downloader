# Fathom Video Downloader

This script allows you to download videos from Fathom using the m3u8 playlist URL. It provides a progress indicator based on the number of video chunks being downloaded.

## Prerequisites

- Python 3.6 or higher
- ffmpeg installed and available in your system's PATH.
- `requests` and `python-dotenv` Python packages. You can install them using pip:
  ```bash
  pip install requests python-dotenv
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

2.  **Run the script:**

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

    ```bash
    python fathom.py https://fathom.video/share/z9R_xcgWVJhQsfQEagyA3toiGbeUtuHj
    ```
    This will download the video and save it using the video ID as the filename.

## How it works

The script performs the following steps:

1.  Loads environment variables from the `.env` file.
2.  Parses command-line arguments using `argparse`.
3.  Constructs the full m3u8 URL.
4.  Fetches the content of the m3u8 playlist file.
5.  Parses the m3u8 content to get a list of video chunk URLs and counts the total number of chunks.
6.  Determines the output filename based on the provided `--output-name` or the video ID.
7.  Determines the output directory from the `OUTPUT_DIR` environment variable or uses the current directory.
8.  Creates the output directory if it doesn't exist.
9.  Constructs the full output path for the video file.
10. Executes the `ffmpeg` command to download the video using the m3u8 URL.
11. Captures the stderr output from `ffmpeg` in real-time.
12. Parses the stderr output to identify when each video chunk is being read.
13. Displays a progress indicator showing the number of chunks downloaded out of the total.
14. Reports the download completion or any errors encountered during the process.