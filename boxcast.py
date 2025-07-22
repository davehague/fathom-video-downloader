# boxcast.py

import sys
import subprocess
from urllib.parse import urlparse, parse_qs
import os
import requests
import re
import argparse
from dotenv import load_dotenv


def extract_boxcast_id(url):
    """Extract the BoxCast video ID from various URL formats"""
    # Handle embed URLs like: https://boxcast.tv/view-embed/f5w8izqx5gtxc57vkhkf?...
    if "view-embed" in url:
        match = re.search(r'/view-embed/([a-zA-Z0-9]+)', url)
        if match:
            return match.group(1)
    
    # Handle other potential URL formats
    match = re.search(r'/([a-zA-Z0-9]+)(?:\?|$)', url)
    if match:
        return match.group(1)
    
    return None


def get_m3u8_url_from_embed(embed_url):
    """Fetch the embed page and extract the m3u8 URL"""
    try:
        response = requests.get(embed_url)
        response.raise_for_status()
        
        # Method 1: Look for m3u8 URL in the view data
        view_pattern = r'"view":\s*{[^}]*"playlist":\s*"([^"]+)"'
        view_match = re.search(view_pattern, response.text)
        if view_match:
            m3u8_url = view_match.group(1)
            # Decode HTML entities and Unicode escapes
            m3u8_url = m3u8_url.replace('\\u0026', '&')
            m3u8_url = m3u8_url.replace('&amp;', '&')
            return m3u8_url
        
        # Method 2: General m3u8 pattern search as fallback
        m3u8_pattern = r'(https://play\.boxcast\.com/[^"\']+\.m3u8[^"\']*)'
        matches = re.findall(m3u8_pattern, response.text)
        
        if matches:
            # Decode HTML entities and Unicode escapes
            m3u8_url = matches[0]
            m3u8_url = m3u8_url.replace('\\u0026', '&')
            m3u8_url = m3u8_url.replace('&amp;', '&')
            return m3u8_url
        else:
            print("Could not find m3u8 URL in the embed page")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching embed page: {e}")
        return None


def download_boxcast_video(m3u8_url, output_path):
    """Download video using ffmpeg"""
    print(f"Downloading video from: {m3u8_url}")
    
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
                print("Try getting a fresh URL from the BoxCast page.")
            
            raise subprocess.CalledProcessError(process.returncode, command)
        
        print(f"Download complete: {output_path}")
        
    except subprocess.CalledProcessError as e:
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    
    parser = argparse.ArgumentParser(description="Download a BoxCast video.")
    parser.add_argument(
        "boxcast_url", 
        help="The BoxCast URL (either embed URL or direct m3u8 URL)."
    )
    parser.add_argument(
        "--output-name",
        help="Optional name for the output video file (without extension).",
    )
    args = parser.parse_args()
    
    boxcast_url = args.boxcast_url
    output_name = args.output_name
    
    # Check if it's already an m3u8 URL
    if '.m3u8' in boxcast_url:
        m3u8_url = boxcast_url
        # Try to extract video ID from the m3u8 URL for default filename
        video_id = "boxcast_video"
        id_match = re.search(r'/p/([a-zA-Z0-9]+)/', boxcast_url)
        if id_match:
            video_id = id_match.group(1)
    else:
        # It's an embed URL, fetch the page to get m3u8
        print("Fetching m3u8 URL from embed page...")
        m3u8_url = get_m3u8_url_from_embed(boxcast_url)
        if not m3u8_url:
            print("Failed to extract m3u8 URL from the provided BoxCast URL")
            sys.exit(1)
        
        # Extract video ID for default filename
        video_id = extract_boxcast_id(boxcast_url)
        if not video_id:
            video_id = "boxcast_video"
    
    # Determine the final output filename
    if output_name:
        final_output_name = output_name
    else:
        final_output_name = video_id
    
    output_filename = f"{final_output_name}.mp4"
    
    # Get output directory from environment variable, default to current directory
    output_dir = os.getenv("OUTPUT_DIR", ".")
    os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn't exist
    
    full_output_path = os.path.join(output_dir, output_filename)
    
    download_boxcast_video(m3u8_url, full_output_path)