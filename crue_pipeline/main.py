# import sys
# import os
# from llm_setup import llm
# # Absolute path to your EmotionAgentApp root directory
# ROOT_DIR = os.path.abspath(os.path.join(os.getcwd(), '..'))
# if ROOT_DIR not in sys.path:
#     sys.path.insert(0, ROOT_DIR)

# from tools.recommender_tools import tools
# from emotion_detector.detect_emotion import get_emotion
# from crewai import Agent, Task, Crew

# emotion = get_emotion()  # Replace with real-time detection

# recommendation_agent = Agent(
#     role="Recommender",
#     goal="Suggest actions based on emotional state",
#     backstory="You help people feel better by launching the right app or giving suggestions.",
#     verbose=True,
#     allow_delegation=False,
#     tools=tools
# )

# task = Task(
#     description=f"The user is feeling {emotion}. Suggest or launch a suitable app.",
#     agent=recommendation_agent
# )

# crew = Crew(
#     agents=[recommendation_agent],
#     tasks=[task],
#     verbose=True
# )

# crew.kickoff()

#########################################################################################################
import re
import sys
import os
import json
import time

# Set root directory for imports
ROOT_DIR = os.path.abspath(os.path.join(os.getcwd(), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


from emotion_detector.detect_emotion import get_dominant_emotion
from emotion_agent import recommend_action
from execution_agent import execute_action
from notification_code import notification_show
from selection_window import selection_window

# if __name__ == "__main__":
#     print("Monitoring user for dominant emotion over 60 seconds...")
#     emotion = get_dominant_emotion(duration=60)
#     print(f"Dominant Emotion: {emotion}")

#     print(f"\nAgent is recommending actions for: {emotion} emotion...")
#     recommendations_raw_output = recommend_action(emotion)

#     recommendations = []
#     # Extract tool name from suggestion (basic logic, or improve with parsing)
#     # tool_candidates = ["open_spotify", "play_youtube_relaxing_video", "open_game", "open_social_media", "write_journal_entry"]
#     # tool_found = next((tool for tool in tool_candidates if tool in suggestion.lower()), None)

#     # if tool_found:
#     #     print(f"\nExecuting suggested tool: {tool_found}")
#     #     result = execute_action(tool_found)
#     #     print("Execution Result:", result)
#     # else:
#     #     print("No matching tool found in the recommendation.")
#     json_match = re.search(r'(\[.*?\])\s*$', recommendations_raw_output.strip(), re.DOTALL)
    
#     if json_match:
#         json_string = json_match.group(1) # Extract the captured JSON string
#         try:
#             recommendations = json.loads(json_string)
#         except json.JSONDecodeError as e:
#             print(f"Error: Could not parse recommendations from agent. JSONDecodeError: {e}")
#             print("Problematic JSON string for parsing:", json_string)
#             print("Agent raw output (full):", recommendations_raw_output)
#     else:
#         print("Error: No valid JSON array found in agent's output.")
#         print("Agent raw output (full):", recommendations_raw_output)
#     # --- End of JSON Extraction Logic ---

#     if recommendations:
#         print("\nHere are some suggested activities to help you:")
#         for i, rec in enumerate(recommendations):
#             # Using .get() with default values to prevent KeyError if a key is missing
#             print(f"{i + 1}. {rec.get('title', 'No Title')}: {rec.get('description', 'No Description')}")
        
#         while True:
#             try:
#                 user_choice = input("Enter the number of the activity you'd like to do (or 'q' to quit): ").strip().lower()
#                 if user_choice == 'q':
#                     print("Exiting without performing an action.")
#                     break
                
#                 choice_index = int(user_choice) - 1
#                 if 0 <= choice_index < len(recommendations):
#                     selected_recommendation = recommendations[choice_index]
#                     tool_to_execute = selected_recommendation.get('tool_name')
#                     # Get tool_params, defaulting to an empty dictionary if not present
#                     tool_params = selected_recommendation.get('tool_params', {})
                    
#                     if tool_to_execute:
#                         print(f"\nExecuting: {selected_recommendation.get('title', 'Selected Action')}...")
#                         # Pass the tool_params dictionary as keyword arguments
#                         result = execute_action(tool_to_execute, **tool_params)
#                         print("Execution Result:", result)
#                         break # Exit loop after successful execution
#                     else:
#                         print("Selected recommendation does not have a 'tool_name' defined.")
#                 else:
#                     print("Invalid choice. Please enter a number within the range.")
#             except ValueError:
#                 print("Invalid input. Please enter a number or 'q'.")
#             except Exception as e:
#                 print(f"An unexpected error occurred during user interaction or execution: {e}")
#     else:
#         print("No recommendations were generated by the agent or could not be parsed.")




def display_recommendations(recommendations_list):
    """
    Displays the list of recommendations to the user.
    Returns True if recommendations were displayed, False otherwise.
    """
    if not recommendations_list:
        print("\nNo recommendations were generated by the agent.")
        return False
    else:
        print("\nHere are some suggested activities to help you:")
        for i, rec in enumerate(recommendations_list):
            # Use .get() with a default value to safely access keys
            title = rec.get("title", "No Title")
            description = rec.get("description", "No Description")
            print(f"{i + 1}. {title}: {description}")
        return True

def get_user_choice(num_options):
    """
    Prompts the user to select an activity from the displayed list.
    Returns the 0-indexed choice or None if the user quits.
    """
    try:
        choice = input(f"Enter the number of the activity you'd like to do (1-{num_options}), or 'q' to quit: ").strip().lower()
        if choice == 'q':
            return None
        
        choice_int = int(choice)
        if 1 <= choice_int <= num_options:
            return choice_int - 1 # Convert to 0-indexed list
        else:
            print("Invalid number. Please enter a number within the displayed range.")
    except ValueError:
        print("Invalid input. Please enter a number or 'q'.")

def run_emotion_recommender_loop():
    """
    Main loop to continuously detect emotion, get recommendations,
    allow user selection, and execute chosen actions.
    """
    user_input = input("\nHow are you feeling today? (Type 'q' to quit, or 's' to start emotion monitoring): ").strip()
    if user_input.lower() == 'q':
        print("Exiting application. Goodbye!")
    elif user_input.lower() == 's':
        print("Monitoring user for dominant emotion over 60 seconds...")
        emotion = get_dominant_emotion(duration=10)
        print(f"Dominant Emotion: {emotion}")
    else:
        # If user just types an emotion directly, use that
        emotion = user_input
        print(f"Using provided emotion: {emotion}")


    print(f"\nAgent is recommending actions for: {emotion} emotion...")
    recommendations_raw_output = recommend_action(emotion)

    print(f"Recommendation output: {recommendations_raw_output}")

    recommendations = []
    
    # --- Robust JSON Extraction Logic ---
    # This regex looks for the first complete JSON array '[...]'
    # It's flexible to ignore any text before or after the JSON.
    json_match = re.search(r'\[.*?\]', recommendations_raw_output.strip(), re.DOTALL)
    
    if json_match:
        json_string = json_match.group(0) # Extract the captured JSON string
        try:
            recommendations = json.loads(json_string)
            print(f"Json string: {recommendations}")
        except json.JSONDecodeError as e:
            print(f"Error: Could not parse recommendations from agent. JSONDecodeError: {e}")
            print(f"Problematic JSON string for parsing:\n{json_string}")
            print(f"Agent raw output (full):\n{recommendations_raw_output}")
    else:
        print("Error: No complete JSON array found in agent's output.")
        print(f"Agent raw output (full):\n{recommendations_raw_output}")
    # --- End of JSON Extraction Logic ---

    # If recommendations were successfully parsed and displayed
    if display_recommendations(recommendations):

        user_choice = notification_show()
        
        if(user_choice):

            #choice_index = get_user_choice(len(recommendations))

            choice_index = selection_window(recommendations)
            
            if choice_index is not None: # User made a selection
                selected_recommendation = recommendations[choice_index]
                tool_name = selected_recommendation.get('tool_name')
                # Get tool_params, defaulting to an empty dictionary if not present
                tool_params = selected_recommendation.get('tool_params')
            
                if tool_name:
                    print(f"\nExecuting: {selected_recommendation.get('title', 'Selected Action')}...")

                    print(f"Print tool: {tool_name} and tool parameter: {tool_params}") 
                    # Pass tool_params as a dictionary directly to execute_action
                    result = execute_action(tool_name, tool_params) 
                    print(f"Execution Result: {result}")
                else:
                    print("Error: Selected recommendation has no 'tool_name' defined.")
            else:
                print("No activity selected for execution this round.")
        else:
            print("No activity selected for execution this round.")
    # If no recommendations were displayed (e.g., parsing failed)
    else:
        print("Unable to proceed with recommendations this round.")

if __name__ == "__main__":
    run_emotion_recommender_loop()