import base64
import ollama
import requests
from utils.desktop import capture_desktop
import requests

# def task_detection_agent():
#     try:
#         # Capture screenshot as a base64 string (possibly with prefix)
#         screenshot = capture_desktop()
#         if not screenshot:
#             raise ValueError("Failed to capture screenshot")

#         # Remove data URI prefix if present
#         if screenshot.startswith('data:image'):
#             screenshot = screenshot.split(',')[1]

#         # Validate base64 string (optional, for debugging)
#         try:
#             base64.b64decode(screenshot)
#         except Exception as decode_err:
#             raise ValueError(f"Invalid base64 screenshot: {decode_err}")

#         # Send the raw base64 string (no prefix) to Ollama
#         response = ollama.generate(
#             model="llava:7b",
#             prompt="Describe user's current activity. Focus on software and tasks.",
#             images=[screenshot]
#         )
#         print("Response from Ollama:", response)
#         print(f"Detected task: {response['response'].strip()}")
#         return {"detected_task": response["response"].strip()}

#     except Exception as e:
#         print(f"Error detecting task: {str(e)}")
#         return {"detected_task": "unknown"}

# if __name__ == "__main__":
#     task_detection_agent()


def task_detection_agent(state):
    try:
        if state.average_emotion == "neutral":
            print("[Agent] No task detection needed for neutral emotion.")
            return {"detected_task": "No Need to Detect Task"}
        # Capture screenshot as a base64 string (possibly with prefix)
        screenshot = capture_desktop()
        if not screenshot:
            raise ValueError("Failed to capture screenshot")
        # Remove data URI prefix if present
        if screenshot.startswith('data:image'):
            screenshot = screenshot.split(',')[1]

        # Validate base64 string (optional, for debugging)
        try:
            base64.b64decode(screenshot)
        except Exception as decode_err:
            raise ValueError(f"Invalid base64 screenshot: {decode_err}")

        # Send the raw base64 string (no prefix) to Ollama
        # response = ollama.generate(
        #     model="llava:7b",
        #     prompt="Describe user's current activity. Focus on software and tasks.",
        #     images=[screenshot]
        # )
        headers = {
            "Connection": "close",  # Disable keep-alive
            "Content-Type": "application/json"
        }
        response = requests.post(
            "https://5a1b-192-248-50-253.ngrok-free.app/api/generate",
            headers=headers,
            json={
                "model": "llava:7b",
                "prompt": "Describe user's current activity. Focus on software and tasks.",
                "images": [screenshot],
                "stream": False
            }
        )

        # Handle HTTP errors
        if response.status_code != 200:
            print(f"API error ({response.status_code}): {response.text[:100]}...")
            return {"detected_task": "unknown"}

        # Parse JSON response
        response_data = response.json()
        detected_task = response_data.get('response', '').strip()
        print(f"Detected task: {detected_task}")
        return {"detected_task": detected_task}

    except Exception as e:
        print(f"Error detecting task: {str(e)}")

        return {"detected_task": "unknown"}
    
if __name__ == "__main__":
    task_detection_agent()

