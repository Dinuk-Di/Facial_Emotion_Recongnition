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
from openai import OpenAI
from dotenv import load_dotenv
import os
import json, pickle
from pydantic import BaseModel, Field
from old_utils.state import app_state, pickle_load, pickle_save

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

class AgentState(BaseModel):
    emotions: List[str]
    average_emotion: Optional[str]
    detected_task: Optional[str]
    recommendation: Optional[str]
    recommendation_options: Optional[List[Dict[str,str]]] # type: ignore
    executed: Optional[bool]
    action_executed: Optional[str]
    action_time_start: Optional[float]

class AppRecommendation(BaseModel):
    app_name: str
    app_url: str
    search_query: str

class Recommendations(BaseModel):
    recommendation: List[str]
    recommendation_options: List[AppRecommendation]  # type: ignore



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

def extract_json_from_text(text):
    try:
        # Find JSON between ```json and ```
        match = re.search(r'```json\s*(\{.*?\}|\[.*?\])\s*```', text, re.DOTALL)
        if match:
            return match.group(1)

        # If no code block, try to parse whole text
        if text.strip().startswith("{") or text.strip().startswith("["):
            return text.strip()

        raise ValueError("No valid JSON found in text.")
    except Exception as e:
        print("[Agent] JSON extraction failed:", e)
        return None
    
def recommendation_agent(state):
    # if not state.detected_task or "No Need to Detect Task" in state.detected_task:
    #     print("[Agent] No task detected – skipping recommendation.")
    #     return {"recommendation": ["No action needed"], "recommendation_options": []}


    emotion = state.average_emotion
    # task = state.detected_task
    print(f"[Agent] Processing for emotion={emotion!r}")

    negative_emotions = ["Angry", "Sad", "Fear", "Disgust", "Stress", "Boring"]
    if emotion not in negative_emotions:
        print("[Agent] Mood is fine – no recommendation.")
        return {"recommendation": ["No action needed"], "recommendation_options": []}

    conn = get_connection()
    if not conn:
        print("[Agent] DB connection failed – skip recommendation.")
        return {"recommendation": ["No action needed"], "recommendation_options": []}

    available_apps = get_apps(conn)
    print("[Agent] Available apps:", available_apps)
    # prompt = f"""
    #         User feels {emotion} while working on: {task}.
    #         Looking for 3 four-word mood-improvement suggestions.

    #         Installed apps (category|name|path):
    #         {available_apps!r}

    #         Return ONLY valid JSON. No text, no notes. Output must be an array of 3 objects:
    #         - recommendation: exactly four words
    #         - recommendation_options: array of 2 items each with:
    #             app_name (str),
    #             app_url (URL or local path),
    #             search_query (str, only for web apps),
    #             is_local (bool)
    #         Conditions to check seriously before returning:
    #         - Each recommendation must have 2 app options.
    #         - No duplicates, do not use webapp if local app is available in installed apps.
    #         - All URLs must start with "https://" and if we can use a search query in the given app then append <search_query> token where suitable since each app search query is different from one another . 
    #         - Each local app sets `is_local: true`.
    #         """

    prompt = f"""
            You are a recommendation engine.

            Context:
            - User feels: "{emotion}"
            - Available installed apps (format: category | name | path):
            {available_apps!r}

            Goal:
            Generate EXACTLY 3 mood-improvement suggestions, each consisting of:
            - recommendation: A phrase of exactly FOUR words.
            - recommendation_options: An array of EXACTLY 2 options per recommendation. Each option must include:
                - app_name: (string)
                - app_url: (either a valid HTTPS URL for web apps OR local file path for installed apps)
                - search_query: (string, required only for web apps)
                - is_local: (true if app is installed locally, false if web)

            STRICT RULES:
            1. Output ONLY valid JSON — no extra text, no explanations, no markdown.
            2. JSON format: An array of 3 objects with keys: recommendation, recommendation_options.
            3. Each recommendation must have TWO different apps (no duplicates across or within).
            4. Prefer local apps over web apps if available.
            5. For web apps:
            - All URLs must start with "https://".
            - Use "<search_query>" placeholder in the app_url instead of inserting actual query.
            - Example web apps are YouTube, Spotify, Online Game (https://poki.com/), MyFlixer (https://myflixerz.to/).
            6. For local apps:
            - Use given path as app_url and set is_local = true.
            - search_query is empty
            7. Don't use same app in multiple recommendations.
            8. Each recommendation must be exactly 4 words, meaningful, and mood-impro
            

            Example of expected structure (do NOT include this in response):
            [
            {{
                "recommendation": "Take a quick break",
                "recommendation_options": [
                {{
                    "app_name": "Spotify",
                    "app_url": "https://open.spotify.com/search/<search_query>",
                    "search_query": "relaxing music",
                    "is_local": false
                }},
                {{
                    "app_name": "KMPlayer",
                    "app_url": "C:\\\\Program Files\\\\KMPlayer 64X\\\\KMPlayer.exe",
                    "search_query": "",
                    "is_local": true
                }}
                ]
            }}
            ]

            Now, produce the final JSON output:
            """


    full_schema = RecommendationList.model_json_schema()

    try:
        # res = requests.post(
        #     url="https://openrouter.ai/api/v1/chat/completions",
        #     headers={
        #         "Authorization": f"Bearer {QWEN_API_KEY}",
        #         "Content-Type": "application/json"
        #     },
        #     data=json.dumps({
        #         "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",
        #         "messages": [
        #             {"role": "system", "content": "You are an assistant. Output must be valid JSON only."},
        #             {"role": "user", "content": prompt}
        #         ],
        #         "response_format": {
        #             "type": "json_schema",
        #             "json_schema": {
        #                 "name": "recommendation_list",
        #                 "strict": True,
        #                 "schema": full_schema
        #             }
        #         },
        #         "structured_outputs": True
        #     }
        # ))

        schema = {
            "type": "object",
                    "properties": {
                        "listofRecommendations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "recommendation": {"type": "string"},
                                    "recommendation_options": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "app_name": {"type": "string"},
                                                "app_url": {"type": "string"},
                                                "search_query": {"type": "string"},
                                                "is_local": {"type": "boolean"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
            }

        res = requests.post(
             "https://d53cb0fd37cb.ngrok-free.app/api/generate",  # Use local endpoint
            headers={"Content-Type": "application/json"},
            json={
                "model": "qwen3:4b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2},
                "format": schema    
            }
        )


        print("[Agent] API response:", res.json())
        if res.status_code != 200:
            print(f"[Agent] API returned status {res.status_code}: {res.text[:200]}")
            return {"recommendation": ["No action needed"], "recommendation_options": []}

        # raw_content = res.json()["choices"][0]["message"]["content"]
        raw_content = res.json()["response"]
        print("Raw Response Content:", raw_content)

        try:
            parsed_data = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
        except json.JSONDecodeError:
            print("[Agent] Failed to decode JSON.")
            return {"recommendation": ["No action needed"], "recommendation_options": []}

        if "listofRecommendations" not in parsed_data or not isinstance(parsed_data["listofRecommendations"], list):
            print("[Agent] Parsed data is not a valid list of dicts.")
            return {"recommendation": ["No action needed"], "recommendation_options": []}

        try:
            recommendation_objects = [RecommendationResponse(**item) for item in parsed_data["listofRecommendations"]]
            app_state.recommendations = parsed_data["listofRecommendations"]
        except Exception as e:
            print("[Agent] Exception parsing recommendation objects:", e)
            return {"recommendation": ["No action needed"], "recommendation_options": []}

        resp_data = RecommendationList(listofRecommendations=recommendation_objects)

        # Extract recommendations
        recommendations_list = [rec.recommendation for rec in resp_data.listofRecommendations]
        recommendation_options_list = [rec.recommendation_options for rec in resp_data.listofRecommendations]

        print("Final Recommendations:", recommendations_list)
        print("Options:", recommendation_options_list)        
        
        # Update state
        state.recommendation = recommendations_list
        state.recommendation_options = recommendation_options_list

        try:
            for i, recommendation_type in enumerate(recommendations_list):
                for option in recommendation_options_list[i]:
                    recommed_app = option.app_name
                    app_url = option.app_url
                    search_query = option.search_query
                    is_local = option.is_local

                    add_agent_recommendations(
                        conn,
                        1,
                        recommendation_type,
                        recommed_app,
                        app_url,
                        search_query,
                        is_local
                    )
        except Exception as e:
            print("[Agent] Error adding recommendations to DB:", e)


        return {
            "recommendation": recommendations_list,
            "recommendation_options": recommendation_options_list
        }

    except Exception as e:
        print("[Agent] Unexpected error:", e)
        return {
            "recommendation": ["No action needed"],
            "recommendation_options": [],
            "listofRecommendations": RecommendationList(listofRecommendations=[])
        }



def send_blocking_message(title, message):
    MB_OK = 0x0
    ctypes.windll.user32.MessageBoxW(0, message, title, MB_OK)

def task_execution_agent(state):
    recommended_output = state.recommendation
    recommended_options = state.recommendation_options
    
    print("List of Recommendations in task_execution_agent: ", recommended_output)
    print("Recommendation Options in task_execution_agent: ", recommended_options)
    if "No action needed" not in recommended_output:
        app_state.executed = True
        pickle_save()
        print("Task executed: ", app_state.executed)

        while pickle_load().executedApp == False:
            print("waiting for reply..")
            time.sleep(2)

        selectedRecommendation = pickle_load().selectedRecommendation
        selectedApp = pickle_load().selectedApp

        chosen_recommendation = {}

        for i in app_state.recommendations:
            if(i['recommendation'] == selectedRecommendation):
                for j in i['recommendation_options']:
                    if(j['app_name'] == selectedApp):
                        chosen_recommendation = j
                        break
                break

        print("Executed task with recommendation: ", chosen_recommendation)

        app_state.reset()
        pickle_save()

        #chosen_recommendation = send_notification("Recommendations by EMOFI", recommended_output,recommended_options)
        print("Chosen recommendation: ", chosen_recommendation)
        if chosen_recommendation:
            print("Opening recommendations...")
            open_recommendations(chosen_recommendation)
            state.executed = True
            return {
                    "executed": True,
                }
                    
def task_exit_agent(state):
    task_executed = True
    if not state.executed:
        return {"executed": False, "action_time_start": None}
    print("Thread is running")
    while task_executed:
        time.sleep(20)
        task_executed = False
    print("Thread is closed")
    return {"executed": False, "action_time_start": None}


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

# def recommendation_agent(state):

#     if "No Need to Detect Task" in state.detected_task or not state.detected_task:
#         print("[Agent] No task detected, skipping recommendation.")
#         return {"recommendation": "No action needed"}
    
#     emotion = state.average_emotion.lower()
#     detected_task = state.detected_task
#     print(f"[Agent] Calculating recommendation for emotion: {emotion} and task: {detected_task}")

#     negative_emotions = ["angry", "sad", "fear", "disgust", "stress","boring"]

#     if emotion not in negative_emotions:
#         print("You are in a good mood")
#         return {
#             "recommendation": "No action needed",
#             "recommendation_options": []
#         }

#     print("⚠️ Since the emotion is a negative one. Let's proceede next steps.")
#     if emotion in negative_emotions:
#         print(f"[Agent]{emotion}")  

#     # get available apps from database
#     conn = get_connection()
#     if not conn:    
#         print("[Agent] Failed to connect to the database.")
#         return {"recommendation": "No action needed", "recommendation_options": []}
#     print(f"[Agent] Fetching apps for emotion: {emotion}")
#     available_apps = get_apps_by_emotion(conn, emotion)

#     prompt = f"""
#         User is feeling {emotion} and is currently working on the screen task: {detected_task}.
#         User is looking for a way to improve mood.

#         Here are the locally installed apps and their paths that can help:
#         {available_apps}

#         There are two outputs. 
#         - 'recommendation': Suggestion to improve the mood. Give the most suitable 3 recommandations each containing 4 words, according to the selected apps and online available apps(like youtube, spotify, online games like free sites). 
#         - 'recommendation_options': list of 2 apps that are available locally or online.
#         The recommendation_options should be apps. It contains 3 parameters:
#         - app_name: Name of the app
#         - app_url: URL of the app ('https://xxxxxxx.com') or path of the app from above available_apps
#         - search_query: If the app is a web browser, give a suitable search query to find the app.
#         Response Formate:
#         '''[
#             {{
#                 "recommendation": "",
#                 "recommendation_options": [{{
#                     "app_name": "",
#                     "app_url": "",
#                     "search_query": ""
#                 }}],
                
#             }}]'''
#         Respond ONLY with the exact phrase from the list.
#         """
    
#     # Please install OpenAI SDK first: `pip3 install openai`

#         # 

#         # 

        

#         # 

#     try:
#         # response = requests.post(
#         #     "https://087f647be26e.ngrok-free.app/api/generate",  # Use local endpoint
#         #     headers={"Content-Type": "application/json"},
#         #     json={
#         #         "model": "qwen3:4b",
#         #         "prompt": prompt,
#         #         "stream": False,
#         #         "options": {"temperature": 0.2},
                
#         #     }
#         # )

#         client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

#         response = client.chat.completions.create(
#             model="deepseek-reasoner",
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant"},
#                 {"role": "user", "content": "Hello"},
#             ],
#             stream=False
#         )

#         print(response.choices[0].message.content)

        
#         # Handle HTTP errors
#         if response.status_code != 200:
#             print(f"API error ({response.status_code}): {response.text[:100]}...")
#             return {"recommendation": "No action needed"}
            
#         response_data = response.json()
#         print("Response from Ollama:", response_data)
#         # Clean response from <think> tags if present
#         recommendation, recommendation_options = parse_llm_response(response_data.get('response', ''))
        
#         # Validate response format
#         valid_recommendation = ["Listen to songs", "Watch funny videos", "Chat with friends", "Call a friend", "Play Quick game", "Do painting"]
        
#         if recommendation not in valid_recommendation:
#             print(f"[Warning] Invalid recommendation: {recommendation}")
#             recommendation = "No action needed"
        
#         # Store in state
#         state.recommendation = recommendation
#         state.recommendation_options = recommendation_options
#         print(f"Recommendation: {recommendation}")
#         print(f"Recommendation options: {recommendation_options}")
#         return {
#             "recommendation": recommendation,
#             "recommendation_options": recommendation_options
#         }
        
#     except Exception as e:
#         print("[Agent] Error parsing response:", e)
#         recommendation = "No action needed"
#         recommendation_options = []

# Define structured output model
class AppRecommendation(BaseModel):
    app_name: str = Field(description="Name of recommended application")
    app_url: str = Field(description="URL or local path of the application")
    search_query: str = Field(description="Search query if web-based application")

class RecommendationResponse(BaseModel):
    recommendations: List[str] = Field(description="Three 4-word mood improvement suggestions")
    recommendation_options: List[AppRecommendation] = Field(description="Two app recommendations")

def recommendation_agent(state: Any) -> Dict[str, Any]:
    # Skip if no task detected
    if "No Need to Detect Task" in state.detected_task or not state.detected_task:
        return {"recommendations": [], "recommendation_options": []}
    
    emotion = state.average_emotion.lower()
    negative_emotions = ["angry", "sad", "fear", "disgust", "stress", "boring"]
    
    # Skip if positive emotion
    if emotion not in negative_emotions:
        return {"recommendations": [], "recommendation_options": []}
    
    # Get available apps from database
    conn = get_connection()
    if not conn:
        return {"recommendations": [], "recommendation_options": []}
    
    available_apps = get_apps_by_emotion(conn, emotion)
    
    # Define tool for app retrieval
    tools = [
        {
            "name": "get_available_apps",
            "description": "Retrieve locally installed applications for mood improvement",
            "parameters": {
                "type": "object",
                "properties": {
                    "emotion": {"type": "string", "description": "Current user emotion"}
                },
                "required": ["emotion"]
            },
            "func": lambda emotion: available_apps  # Directly return pre-fetched apps
        }
    ]
    
    # Create LLM instance
    llm = Ollama(
        model="qwen3:4b",
        base_url="https://087f647be26e.ngrok-free.app",
        temperature=0.2
    )
    
    # Define prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You're a mood improvement assistant. Generate recommendations based on user's emotion: {emotion} and current task: {task}."),
        ("human", "Suggest 3 mood improvement activities (4 words max) and recommend 2 apps from local: {apps} or web services like YouTube/Spotify.")
    ])
    
    # Create react agent
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
        output_schema=RecommendationResponse
    )
    
    # Execute agent
    response = agent.invoke({
        "emotion": emotion,
        "task": state.detected_task,
        "apps": str(available_apps)
    })
    
    # Process and validate response
    valid_recommendations = ["Listen to songs", "Watch funny videos", "Chat with friends", 
                            "Call a friend", "Play Quick game", "Do painting"]
    
    recommendations = [
        rec for rec in response["recommendations"][:3] 
        if rec in valid_recommendations
    ]
    
    # Ensure we have exactly 3 recommendations
    if len(recommendations) < 3:
        recommendations += ["Take deep breaths"] * (3 - len(recommendations))
    
    # Format app recommendations
    recommendation_options = []
    for app in response["recommendation_options"][:2]:
        recommendation_options.append({
            "app_name": app.app_name,
            "app_url": app.app_url,
            "search_query": app.search_query
        })
    
    # Update state
    state.recommendations = recommendations
    state.recommendation_options = recommendation_options
    
    return {
        "recommendations": recommendations,
        "recommendation_options": recommendation_options
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


