import sys
import time
from pyngrok import ngrok

def start_tunnel():
    # Set auth token
    ngrok.set_auth_token("38hj6vtOpHdIfAxItq7g9HUrcTA_6eSY5P5VrNoKCim25HCJW")

    # Kill any existing tunnels
    ngrok.kill()
    
    # Open a HTTP tunnel on the default port 5000
    public_url = ngrok.connect(5003)
    print("=" * 60)
    print(f" * Public URL: {public_url}")
    print("=" * 60)
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down tunnel...")
        ngrok.kill()

if __name__ == "__main__":
    start_tunnel()
