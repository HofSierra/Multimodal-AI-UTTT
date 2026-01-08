from pyngrok import ngrok
import time
import requests

PORT = 8000 

def check_local_api():
    try:
        requests.get(f"http://localhost:{PORT}")
        return True
    except requests.exceptions.ConnectionError:
        return False

try:
    if not check_local_api():
        print(f"No API detected on localhost:{PORT}")

    public_url = ngrok.connect(PORT).public_url
    
    print(f"Forwarding: {public_url} -> http://localhost:{PORT}")
    print(f"\nCOPY THIS TO TTT_bot.py:")
    print(f"self.api_url = \"{public_url}/predict_move\"")
    
    while True:
        time.sleep(1)
except Exception as e:
    print(f"Error: {e}")