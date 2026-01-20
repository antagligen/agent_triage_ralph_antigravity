import requests
import json
import sys

def verify_streaming():
    url = "http://localhost:8000/chat"
    payload = {"message": "Troubleshoot ACI tenant ABC"}

    print(f"Connecting to {url}...")
    try:
        with requests.post(url, json=payload, stream=True) as response:
            if response.status_code != 200:
                print(f"Error: Status code {response.status_code}")
                print(response.text)
                return False

            print("Connected. Listening for events...")
            buffer = ""
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    text = chunk.decode('utf-8')
                    buffer += text

                    while "\n\n" in buffer:
                        event_str, buffer = buffer.split("\n\n", 1)
                        print(f"--- Event Received ---\n{event_str}\n----------------------")

                        if "event: thought" in event_str:
                            print("SUCCESS: Thought event received.")
    except Exception as e:
        print(f"Exception: {e}")
        return False

    return True

if __name__ == "__main__":
    verify_streaming()
