import os
import sys
import time
import subprocess
import requests
import re
from pathlib import Path

# Configuration
PORT = 5003
CLOUDFLARED_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
SCRIPT_DIR = Path(__file__).parent
BIN_NAME = "cloudflared.exe"
BIN_PATH = SCRIPT_DIR / BIN_NAME

def download_cloudflared():
    """Download cloudflared binary if it doesn't exist."""
    if BIN_PATH.exists():
        print(f"Found existing cloudflared at {BIN_PATH}")
        return

    print(f"Downloading cloudflared from {CLOUDFLARED_URL}...")
    try:
        response = requests.get(CLOUDFLARED_URL, stream=True)
        response.raise_for_status()
        
        with open(BIN_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")
    except Exception as e:
        print(f"Error downloading cloudflared: {e}")
        sys.exit(1)

def start_tunnel():
    """Start the cloudflare tunnel and parse the URL."""
    print(f"Starting Cloudflare Tunnel on port {PORT}...")
    
    # Command to run cloudflared
    cmd = [str(BIN_PATH), "tunnel", "--url", f"http://localhost:{PORT}"]
    
    # Start the process
    # We need to capture stderr because cloudflared prints the URL there
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1
    )

    print("Waiting for public URL...")
    
    public_url = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    try:
        # Read stderr line by line to find the URL
        while True:
            # Check if process is still running
            if process.poll() is not None:
                print("Cloudflared process ended unexpectedly.")
                print(process.stderr.read())
                break

            # Read a line from stderr (where logs usually go)
            line = process.stderr.readline()
            if not line:
                time.sleep(0.1)
                continue
                
            print(f"Log: {line.strip()}")
            
            match = url_pattern.search(line)
            if match:
                public_url = match.group(0)
                print("\n" + "=" * 60)
                print(f" * Public URL: {public_url}")
                print("=" * 60 + "\n")
                
                # Write to file
                with open("satalite_url.txt", "w") as f:
                    f.write(public_url)
                    
                # We found the URL, but we need to keep the process running
                # Stop reading lines to avoid blocking if no more output comes suitable 
                # for this simple script, or just loop to verify liveness
                break
        
        # Keep alive
        while process.poll() is None:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down tunnel...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

if __name__ == "__main__":
    download_cloudflared()
    start_tunnel()
