# import ollama
# from collections import Counter
# from utils.desktop import capture_desktop
# from utils.notifications import send_notification, execute_task

# def average_emotion_agent(state: dict):
#     """Calculate most frequent emotion"""
#     if not state["emotions"]:
#         return {"average_emotion": "neutral"}
    
#     counter = Counter(state["emotions"])
#     most_common = counter.most_common(1)[0][0]
#     print(f"Average emotion: {most_common}")
#     return {"average_emotion": most_common}

# # def task_detection_agent():
# #     try:
# #         """Detect desktop activity using VLM"""
# #         screenshot = capture_desktop()
# #         response = ollama.generate(
# #             model="moondream:1.8b",
# #             prompt="Describe user's current activity in 5 words. Focus on software and tasks.",
# #             images=[screenshot]
# #         )
# #         print(f"Detected task: {response['response'].strip()}")
# #         return {"detected_task": response["response"].strip()}
# #     except Exception as e:
# #         print(f"Error detecting task: {str(e)}")
# #         return {"detected_task": "unknown"}

# def recommendation_agent(state: dict):
#     print(f"Calculating recommendation for emotion: {state['average_emotion']}")
#     """Generate recommendations for negative emotions"""
#     negative_emotions = ["angry", "sad", "fear", "disgust", "stress"]
    
#     if state["average_emotion"] not in negative_emotions:
#         return {"recommendation": "No action needed"}
    
#     prompt = f"""
#     User is feeling {state['average_emotion']}
#     Suggest one concrete action to improve mood from this list:
#     - Play music: opens Spotify
#     - Watch funny videos: opens YouTube
#     - Take a break: shows relaxation tips
#     - Quick game: opens a browser game
#     - Nothing
    
#     Respond ONLY with the exact phrase from the list.
#     """
    
#     response = ollama.generate(
#         model="qwen:4b",
#         prompt=prompt,
#         options={"temperature": 0.2}
#     )
#     print("Response from Ollama:", response)
    
#     print(f"Recommendation: {response['response'].strip()}")
#     return {"recommendation": response["response"].strip()}

# def task_execution_agent(state: dict):
#     print(f"Executing recommendation: {state['recommendation']}")
#     """Execute recommended action"""
#     if "No action" in state["recommendation"]:
#         return {"executed": False}
    
#     send_notification(
#         title="Emotion Assistant",
#         message=f"You seem {state['average_emotion']}. Recommendation: {state['recommendation']}"
#     )
#     execute_task(state["recommendation"])
#     print(f"Executed action: {state['recommendation']}")
#     return {"executed": True}

import base64
from collections import Counter
import re
import json
import time
from utils.desktop import capture_desktop
from utils.notifications import send_notification, execute_task
from utils.selection_window import selection_window
from tools.recommender_tools import open_recommendation
from utils.runner_interface import launch_window
import requests
import ctypes
from collections import Counter
import psutil
from typing import Dict, List

launched_apps = {}
opened_browser_instances = []  # Track browser instances we launched
opened_browser_tabs: List[Dict] = []  # Track individual tabs


def average_emotion_agent(state):
    """Calculate most frequent emotion from AgentState model"""
    if not state.emotions:
        return {"average_emotion": "neutral"}
    print(f"[Agent] Emotions: {state.emotions}")
    counter = Counter(state.emotions)
    most_common = counter.most_common(1)[0][0]
    print(f"[Agent] Average emotion: {most_common}")
    return {"average_emotion": most_common}

def parse_llm_response(text):
    try:
        # Clean <think> tags if present
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

        # Extract recommendation
        rec_match = re.search(r'recommendation:\s*(.+)', text)
        recommendation = rec_match.group(1).strip() if rec_match else None

        # Extract recommendation_options (raw list inside [])
        options_match = re.search(r'recommendation_options:\s*\[(.*)\]', text, re.DOTALL)
        options_raw = options_match.group(1).strip() if options_match else ""

        # Convert (app_name: 'X', ...) → {"app_name": "X", ...}
        options = []
        for option_text in re.findall(r'\((.*?)\)', options_raw, re.DOTALL):
            entry = {}
            for kv in option_text.split(','):
                key, val = kv.split(':', 1)
                entry[key.strip()] = val.strip().strip("'\"")
            options.append(entry)

        return recommendation, options

    except Exception as e:
        print("[Agent] Error parsing LLM response block:", e)
        return None, []

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
            "https://087f647be26e.ngrok-free.app/api/generate",
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
        state.detected_task = detected_task
        print(f"Detected task: {detected_task}")
        return {"detected_task": detected_task}

    except Exception as e:
        print(f"Error detecting task: {str(e)}")
        return {"detected_task": "unknown"}

    # prompt = f"""
    # User is feeling {emotion} and is currently working on the screen task: {detected_task}.
    # User is looking for a way to improve mood.
    
    # Suggest one concrete action to improve mood from this list. Try to give listning music and Watch funny videos as a priority:
    # - Play music
    # - Watch funny videos
    # - Take a break
    # - Quick game
    # - If the user is working on a coding task and seems to need a help, then output "Coding Bot"
    # - Nothing
    # Respond ONLY with the exact phrase from the list.
    # """

    # response = ollama.generate(
    #     model="qwen3:4b",
    #     prompt=prompt,
    #     options={"temperature": 0.2}
    # )
    # recommendation = clean_think_tags(response['response'].strip())
    # if not recommendation:
    #     recommendation = "No action needed"
    # print(f"[Agent] Recommendation: {recommendation}")
    # return {"recommendation": recommendation}
    
def recommendation_agent(state):

    if "No Need to Detect Task" in state.detected_task or not state.detected_task:
        print("[Agent] No task detected, skipping recommendation.")
        return {"recommendation": "No action needed"}
    
    emotion = state.average_emotion.lower()
    detected_task = state.detected_task
    print(f"[Agent] Calculating recommendation for emotion: {emotion} and task: {detected_task}")

    negative_emotions = ["angry", "sad", "fear", "disgust", "stress","boring"]

    if emotion not in negative_emotions:
        print("You are in a good mood")
        return {
            "recommendation": "No action needed",
            "recommendation_options": []
        }

    print("⚠️ Since the emotion is a negative one. Let's proceede next steps.")
    if emotion in negative_emotions:
        print(f"[Agent]{emotion}")  

    print("Prompt creation...")

    prompt = f"""
        User is feeling {emotion} and is currently working on the screen task: {detected_task}.
        User is looking for a way to improve mood.

        There are two outputs. 
        - 'recommendation': Suggestion to improve the mood. Give the most suitable option from the list:-["Listen to songs", "Watch funny videos", "Chat with friends", "Call a friend", "Play Quick game", "Do painting"]
        - 'recommendation_options': list of 3 apps that is most suitable to accomplish the given recommendation. 
        The recommendation_options should be apps from the list eg:-[ Discord, Spotify, Paint, Microsoft Teams, Telegram Desktop, Zoom, Youtube, Facebook, Instergram, Microsoft Solitaire Collection] or any other suitable. 
        Response Formate:
        recommendation: Chat with friends
        recommendation_options: [
        (app_name: 'name of the app', text: '3,4 word sentence saying the purpose of the app', app_url: 'https://xxxxxxx.com', search_query: 'If the app through web browser, give a suitable search query'),
        (app_name: '', text: '', app_url: '', search_query: ''),
        (app_name: '' , text: '', app_url: '', search_query: ''),
        ]
        Respond ONLY with the exact phrase from the list.
        """

    try:
        response = requests.post(
            "https://087f647be26e.ngrok-free.app/api/generate",  # Use local endpoint
            headers={"Content-Type": "application/json"},
            json={
                "model": "qwen3:4b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2},
                
            }
        )
        
        # Handle HTTP errors
        if response.status_code != 200:
            print(f"API error ({response.status_code}): {response.text[:100]}...")
            return {"recommendation": "No action needed"}
            
        response_data = response.json()
        print("Response from Ollama:", response_data)
        # Clean response from <think> tags if present
        recommendation, recommendation_options = parse_llm_response(response_data.get('response', ''))
        
        # Validate response format
        valid_recommendation = ["Listen to songs", "Watch funny videos", "Chat with friends", "Call a friend", "Play Quick game", "Do painting"]
        
        if recommendation not in valid_recommendation:
            print(f"[Warning] Invalid recommendation: {recommendation}")
            recommendation = "No action needed"
        
        # Store in state
        state.recommendation = recommendation
        state.recommendation_options = recommendation_options
        print(f"Recommendation: {recommendation}")
        print(f"Recommendation options: {recommendation_options}")
        return {
            "recommendation": recommendation,
            "recommendation_options": recommendation_options
        }
        
    except Exception as e:
        print("[Agent] Error parsing response:", e)
        recommendation = "No action needed"
        recommendation_options = []


def send_blocking_message(title, message):
    MB_OK = 0x0
    ctypes.windll.user32.MessageBoxW(0, message, title, MB_OK)

def task_execution_agent(state):
    recommended_output = state.recommendation
    recommended_options = state.recommendation_options
    
    if "No action needed" not in recommended_output:
        status = send_notification(recommended_output)
        if status:
            #selected_option = selection_window(recommended_options)

            window, app = launch_window(recommended_options)
            app.exec()
            selected_option = window.selectedChoice
            window.close()
            app.quit()

            print("selected option: ", selected_option)
            if selected_option:
                start_time = time.time()
                open_recommendation(selected_option) # Execute the task based on the option
                print("Task is executed")
                return {
                    "executed": True,
                    "action_time_start": start_time
                }
                    
def task_exit_agent(state):
    task_executed = True
    if not state.executed:
        return {"executed": False, "action_time_start": None}
    print("Thread is running")
    while task_executed:
        time.sleep(35)
        task_executed = False
    print("Thread is closed")

    return {"executed": False, "action_time_start": None}

