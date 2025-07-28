import base64
from collections import Counter
import re
from langgraph.graph import StateGraph, END
import requests
from utils.desktop import capture_desktop
from utils.notifications import send_notification, execute_task
import ollama
import ctypes
from collections import Counter
from typing import List, Optional
from pydantic import BaseModel


def run_agent_system(emotions):
    initial_state = AgentState(
        emotions=emotions,
        average_emotion=None,
        detected_task=None,
        recommendation=None,
        executed=False
    )
    agent_workflow = create_workflow()
    return agent_workflow.invoke(initial_state)

class AgentState(BaseModel):
    emotions: List[str]
    average_emotion: Optional[str]
    detected_task: Optional[str]
    recommendation: Optional[str]
    executed: Optional[bool]


def create_workflow():
    workflow = StateGraph(AgentState)
    workflow.add_node("calculate_emotion", average_emotion_agent)
    workflow.add_node("detect_task", task_detection_agent)
    workflow.add_node("generate_recommendation", recommendation_agent)
    workflow.add_node("execute_action", task_execution_agent)
    workflow.set_entry_point("calculate_emotion")
    workflow.add_edge("calculate_emotion", "detect_task")
    workflow.add_edge("detect_task", "generate_recommendation")
    workflow.add_edge("generate_recommendation", "execute_action")
    workflow.add_edge("execute_action", END)
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

def clean_think_tags(text):
    cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned_text.strip()

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
    

def recommendation_agent(state):
    # Early exit if no task detected
    if "No Need to Detect Task" in state.detected_task or not state.detected_task:
        print("[Agent] No task detected, skipping recommendation.")
        return {"recommendation": "No action needed"}
    
    emotion = state.average_emotion.lower()
    detected_task = state.detected_task.lower() if state.detected_task else "unknown"
    print(f"[Agent] Calculating recommendation for emotion: {emotion} and task: {detected_task}")
    
    negative_emotions = ["angry", "sad", "fear", "disgust", "stress", "boring"]
    
    # Exit if not negative emotion
    if emotion not in negative_emotions:
        return {"recommendation": "No action needed"}

    prompt = f"""
        User is feeling {emotion} and is currently working on: {detected_task}.
        Suggest one concrete action to improve mood from this list. Priority order:
        1. Play music
        2. Watch funny videos
        3. Take a break
        4. Quick game
        5. Only if user is coding and needs help: "Coding Bot"
        6. Nothing

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
        recommendation = clean_think_tags(response_data.get('response', '')).strip()
        
        # Validate response format
        valid_actions = [
            "Play music", "Watch funny videos", "Take a break", 
            "Quick game", "Coding Bot", "Nothing"
        ]
        
        if recommendation not in valid_actions:
            print(f"[Warning] Invalid recommendation: {recommendation}")
            recommendation = "No action needed"
        
        # Store in state
        state.recommendation = recommendation
        print(f"Recommendation: {recommendation}")
        return {"recommendation": recommendation}
        
    except Exception as e:
        print(f"Error generating recommendation: {str(e)}")
        return {"recommendation": "No action needed"}



def send_blocking_message(title, message):
    MB_OK = 0x0
    ctypes.windll.user32.MessageBoxW(0, message, title, MB_OK)

def task_execution_agent(state):
    recommendation = state.recommendation
    if "No action" in recommendation:
        return {"executed": False}

    send_blocking_message(
        title="Emotion Assistant",
        message=f"You seem {state.average_emotion}. Recommendation: {recommendation}"
    )
    # This line runs only after user presses OK in the message box
    execute_task(recommendation)
    return {"executed": True}


