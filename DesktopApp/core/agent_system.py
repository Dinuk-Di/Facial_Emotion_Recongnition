from typing import Dict, List, Optional, Any
import base64
from collections import Counter
import re
import time
from langgraph.graph import StateGraph, END
import requests
from utils.desktop import capture_desktop
from ui.notification import send_notification, execute_task
import ollama
import ctypes
from collections import Counter
from typing import List, Optional
from pydantic import BaseModel
from core.recommender_tools import open_recommendation
from old_utils.runner_interface import launch_window
from database.db import get_apps_by_emotion, get_connection
from dotenv import load_dotenv
import os
import json
from pydantic import BaseModel, Field

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")

def run_agent_system(emotions):
    initial_state = AgentState(
        emotions=emotions,
        average_emotion=None,
        detected_task=None,
        recommendation=None,
        recommendation_options= [],
        executed=False,
        action_executed=None,
        action_time_start=0
        
    )
    agent_workflow = create_workflow()
    return agent_workflow.invoke(initial_state)

class AppRecommendation(BaseModel):
    app_name: str = Field(description="Name of recommended application")
    app_url: str = Field(description="URL or local path of the application")
    search_query: str = Field(description="Search query if web-based application")
    is_local: bool = Field(default=False, description="Whether the app is a local executable")


class AgentState(BaseModel):
    emotions: List[str]
    average_emotion: Optional[str]
    detected_task: Optional[str]
    recommendation: Optional[List[str]]  # list of suggestions
    recommendation_options: Optional[List[List[AppRecommendation]]]
    executed: Optional[bool]
    action_executed: Optional[str]
    action_time_start: Optional[float]


class RecommendationResponse(BaseModel):
    recommendation: List[str] = Field(description="4-word mood improvement suggestions")
    recommendation_options: List[AppRecommendation] = Field(description="Two app recommendations")

class RecommendationList(BaseModel):
    listofRecommendations: List[RecommendationResponse] = Field(description="List of 3 recommendations with options")
    



def create_workflow():
    workflow = StateGraph(AgentState)
    workflow.add_node("calculate_emotion", average_emotion_agent)
    workflow.add_node("detect_task", task_detection_agent)
    workflow.add_node("generate_recommendation", recommendation_agent)
    workflow.add_node("execute_action", task_execution_agent)
    workflow.add_node("exit_action", task_exit_agent)
    workflow.set_entry_point("calculate_emotion")
    workflow.add_edge("calculate_emotion", "detect_task")
    workflow.add_edge("detect_task", "generate_recommendation")
    workflow.add_edge("generate_recommendation", "execute_action")
    workflow.add_edge("execute_action", "exit_action")
    workflow.add_edge("exit_action", END)
    return workflow.compile()

def average_emotion_agent(state):
    """Calculate most frequent emotion from AgentState model"""
    if not state.emotions:
        return {"average_emotion": "neutral"}
    print(f"[Agent] Emotions: {state.emotions}")
    counter = Counter(state.emotions)
    most_common = counter.most_common(1)[0][0]
    print(f"[Agent] Average emotion: {most_common}")
    return {"average_emotion": most_common}

# Remove reasoning tags from the response
def clean_think_tags(text):
    cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned_text.strip()


def task_detection_agent(state):
    try:
        if state.average_emotion == "Neutral" or state.average_emotion == "Happy" or state.average_emotion == "Surprise":
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
            "https://fa7a43f295fa.ngrok-free.app/api/generate",
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
    

# def recommendation_agent(state):
#     # Early exit if no task detected
#     if "No Need to Detect Task" in state.detected_task or not state.detected_task:
#         print("[Agent] No task detected, skipping recommendation.")
#         return {"recommendation": "No action needed"}
    
#     emotion = state.average_emotion.lower()
#     detected_task = state.detected_task.lower() if state.detected_task else "unknown"
#     print(f"[Agent] Calculating recommendation for emotion: {emotion} and task: {detected_task}")
    
#     negative_emotions = ["angry", "sad", "fear", "disgust", "stress", "boring"]
    
#     # Exit if not negative emotion
#     if emotion not in negative_emotions:
#         return {"recommendation": "No action needed"}

#     prompt = f"""
#         User is feeling {emotion} and is currently working on: {detected_task}.
#         Suggest one concrete action to improve mood from this list. Priority order:
#         1. Play music
#         2. Watch funny videos
#         3. Take a break
#         4. Quick game
#         5. Only if user is coding and needs help: "Coding Bot"
#         6. Nothing

#         Respond ONLY with the exact phrase from the list.
#     """
#     try:
#         response = requests.post(
#             "https://087f647be26e.ngrok-free.app/api/generate",  # Use local endpoint
#             headers={"Content-Type": "application/json"},
#             json={
#                 "model": "qwen3:4b",
#                 "prompt": prompt,
#                 "stream": False,
#                 "options": {"temperature": 0.2},
                
#             }
#         )
        
#         # Handle HTTP errors
#         if response.status_code != 200:
#             print(f"API error ({response.status_code}): {response.text[:100]}...")
#             return {"recommendation": "No action needed"}
            
#         response_data = response.json()
#         print("Response from Ollama:", response_data)
#         # Clean response from <think> tags if present
#         recommendation = clean_think_tags(response_data.get('response', '')).strip()
        
#         # Validate response format
#         valid_actions = [
#             "Play music", "Watch funny videos", "Take a break", 
#             "Quick game", "Coding Bot", "Nothing"
#         ]
        
#         if recommendation not in valid_actions:
#             print(f"[Warning] Invalid recommendation: {recommendation}")
#             recommendation = "No action needed"
        
#         # Store in state
#         state.recommendation = recommendation
#         print(f"Recommendation: {recommendation}")
#         return {"recommendation": recommendation}
        
#     except Exception as e:
#         print(f"Error generating recommendation: {str(e)}")
#         return {"recommendation": "No action needed"}



# def send_blocking_message(title, message):
#     MB_OK = 0x0
#     ctypes.windll.user32.MessageBoxW(0, message, title, MB_OK)

# def task_execution_agent(state):
#     recommendation = state.recommendation
#     if "No action" in recommendation:
#         return {"executed": False}

#     send_blocking_message(
#         title="Emotion Assistant",
#         message=f"You seem {state.average_emotion}. Recommendation: {recommendation}"
#     )
#     # This line runs only after user presses OK in the message box
#     execute_task(recommendation)
#     return {"executed": True}
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

def recommendation_agent(state):
    if "No Need to Detect Task" in state.detected_task or not state.detected_task:
        print("[Agent] No task detected, skipping recommendation.")
        return {"recommendation": "No action needed", "recommendation_options": []}

    emotion = state.average_emotion
    detected_task = state.detected_task
    print(f"[Agent] Calculating recommendation for emotion: {emotion} and task: {detected_task}")

    negative_emotions = ["Angry", "Sad", "Fear", "Disgust", "Stress", "Boring"]

    if emotion not in negative_emotions:
        print("You are in a good mood")
        return {"recommendation": "No action needed", "recommendation_options": []}

    conn = get_connection()
    if not conn:
        print("[Agent] Failed to connect to the database.")
        return {"recommendation": "No action needed", "recommendation_options": []}

    available_apps = get_apps_by_emotion(conn, emotion)
    print("Available Apps", available_apps)

    prompt = f"""
        User is feeling {emotion} and is currently working on the screen task: {detected_task}.
        User is looking for a way to improve mood.

        Here are the locally installed apps with category, app name and their path:
        {available_apps}

        Output must be ONLY valid JSON. No text, no explanation, no tags and correct key value pairs. When selecting apps, consider:
        1. If the app is a web-based application, use the URL.
        2. If the app is a desktop application, use the path to the executable.
        3. Check the app's is matching for the recommendation.
        4. Search query is applied only for web based applications.
        5. Recommendation options should carry two apps , If there are no suitable local apps available you may select online free application as well.Url should be in this format: "https://xxxxxx.com".
        6. If the path is local, set is_local to true, otherwise false.
        Return the following structure:
        [
            {{
                "recommendation": "<first 4-word suggestion>",
                "recommendation_options": [
                    {{
                        "app_name": "<app name 1>",
                        "app_url": "<app url or path 1>",
                        "search_query": "<search query 1>",
                        "is_local": <true or false>
                    }},
                    {{
                        "app_name": "<app name 2>",
                        "app_url": "<app url or path 2>",
                        "search_query": "<search query 2>",
                        "is_local": <true or false>
                    }}
                ]
            }},
            {{
                "recommendation": "<second suggestion>",
                "recommendation_options": [ ...same as above... ]
            }},
            {{
                "recommendation": "<third suggestion>",
                "recommendation_options": [ ...same as above... ]
            }}
        ]
    """

    try:
        response = requests.post(
            "https://fa7a43f295fa.ngrok-free.app/api/generate",
            headers={"Content-Type": "application/json"},
            json={"model": "qwen3:4b", "prompt": prompt, "stream": False, "options": {"temperature": 0.2}},
        )

        if response.status_code != 200:
            print(f"API error ({response.status_code}): {response.text[:100]}...")
            return {"recommendation": ["No action needed"], "recommendation_options": []}

        raw_response = response.json()["response"]
        print("Raw Response:", raw_response)

        # Extract JSON array from LLM response
        match = re.search(r'\[[\s\S]*\]', raw_response)  # captures first JSON array
        if not match:
            raise ValueError("No valid JSON found in response.")
        clean_json = match.group(0)  # only the JSON array
        json_data = json.loads(clean_json)


        # Convert to list of dictionaries
        json_data = json.loads(clean_json)

        # Validate with Pydantic
        resp_data = RecommendationList(listofRecommendations=[
            RecommendationResponse(**item) for item in json_data
        ])
        print("Parsed Response:", resp_data)

        # Prepare lists for state
        recommendations_list = []
        recommendation_options_list = []

        for rec in resp_data.listofRecommendations:
            recommendations_list.append(rec.recommendations)
            recommendation_options_list.append(rec.recommendation_options)

        # Update state
        state.recommendation = recommendations_list
        state.recommendation_options = recommendation_options_list

        print(f"Recommendations: {recommendations_list}")
        print(f"Recommendation options: {recommendation_options_list}")

        return {
            "recommendation": recommendations_list,
            "recommendation_options": recommendation_options_list
        }

    except Exception as e:
        print("[Agent] Error parsing response:", e)
        return {
            "recommendation": ["No action needed"],
            "recommendation_options": []
        }


def send_blocking_message(title, message):
    MB_OK = 0x0
    ctypes.windll.user32.MessageBoxW(0, message, title, MB_OK)

def task_execution_agent(state):
    recommended_output = state.recommendation
    recommended_options = state.recommendation_options
    print("Recommended output: ", recommended_output)
    if "No action needed" not in recommended_output:
        status = send_notification("Recommendations by EMOFI", recommended_output)
        if status:
            #selected_option = selection_window(recommended_options)
            window, app = launch_window(recommended_options)  # implement suggestions tray simple ui as a drawer from right corner
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


