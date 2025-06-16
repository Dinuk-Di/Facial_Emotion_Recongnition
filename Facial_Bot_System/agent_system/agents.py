import ollama
from collections import Counter
from utils.desktop import capture_desktop
from utils.notifications import send_notification, execute_task

def average_emotion_agent(state: dict):
    """Calculate most frequent emotion"""
    if not state["emotions"]:
        return {"average_emotion": "neutral"}
    
    counter = Counter(state["emotions"])
    most_common = counter.most_common(1)[0][0]
    return {"average_emotion": most_common}

def task_detection_agent(state: dict):
    """Detect desktop activity using VLM"""
    screenshot = capture_desktop()
    response = ollama.generate(
        model="llava",
        prompt="Describe user's current activity in 5 words. Focus on software and tasks.",
        images=[screenshot]
    )
    return {"detected_task": response["response"].strip()}

def recommendation_agent(state: dict):
    """Generate recommendations for negative emotions"""
    negative_emotions = ["angry", "sad", "fear", "disgust", "stress"]
    
    if state["average_emotion"] not in negative_emotions:
        return {"recommendation": "No action needed"}
    
    prompt = f"""
    User is feeling {state['average_emotion']} while {state['detected_task']}.
    Suggest one concrete action to improve mood from this list:
    - Play music: opens Spotify
    - Watch funny videos: opens YouTube
    - Take a break: shows relaxation tips
    - Quick game: opens a browser game
    - Nothing
    
    Respond ONLY with the exact phrase from the list.
    """
    
    response = ollama.generate(
        model="qwen:4b",
        prompt=prompt,
        options={"temperature": 0.2}
    )
    return {"recommendation": response["response"].strip()}

def task_execution_agent(state: dict):
    """Execute recommended action"""
    if "No action" in state["recommendation"]:
        return {"executed": False}
    
    send_notification(
        title="Emotion Assistant",
        message=f"You seem {state['average_emotion']}. Recommendation: {state['recommendation']}"
    )
    execute_task(state["recommendation"])
    return {"executed": True}