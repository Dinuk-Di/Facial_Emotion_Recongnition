# from langchain.tools import tool
# import subprocess
# import os

# @tool
# def open_spotify(dummy: str=None) -> str:
#     """Open Spotify application for music recommendation."""
#     subprocess.Popen(['start', 'spotify'], shell=True)
#     return "Spotify opened."

# @tool
# def open_social_media(dummy: str=None) -> str:
#     """Open instagram for chat recommendation."""
#     os.system('start chrome https://www.instagram.com')
#     return "Instagram opened in browser."

# @tool
# def open_game(dummy: str=None) -> str:
#     """Open game for game recommendation."""
#     game_path = r"C:\\Program Files\\MyGame\\Game.exe"  # Replace with actual game path
#     subprocess.Popen([game_path])
#     return "Game started."
# @tool
# def open_solitaire(dummy: str = None) -> str:
#     """Open the Microsoft Solitaire Collection."""
#     try:
#         os.system("start shell:AppsFolder\Microsoft.MicrosoftSolitaireCollection_8wekyb3d8bbwe!App")
#         return "Solitaire launched successfully."
#     except Exception as e:
#         return f"Failed to launch Solitaire: {e}"

# @tool
# def play_youtube_relaxing_video(dummy: str =None) -> str:
#     """Open YouTube with relaxing music search results."""
#     os.system('start chrome https://www.youtube.com/results?search_query=relaxing+music')
#     return "YouTube opened with relaxing music."

# @tool
# def write_journal_entry( dummy: str=None) -> str:
#     """Append a journal entry to track user's emotion-related activities."""
#     with open("journal.txt", "a") as f:
#         f.write("User was sad. Suggested journaling.\n")
#     return "Added journal entry."

# tools = [open_spotify, open_social_media, open_game, play_youtube_relaxing_video, write_journal_entry]




# tools/recommender_tools.py
from langchain.tools import tool
import subprocess
import time
import os
import urllib.parse # Import for URL encoding to correctly format Youtube queries

@tool
def open_spotify(dummy: str=None) -> str:
    """Open Spotify application for music recommendation."""
    try:
        # 'start spotify' directly calls the application if it's in the PATH or associated
        subprocess.Popen(['start', 'spotify'], shell=True)
        return "Spotify opened successfully."
    except FileNotFoundError:
        return "Failed to open Spotify. Spotify application not found. Please ensure it's installed and accessible."
    except Exception as e:
        return f"Failed to open Spotify: {e}"

@tool
def open_social_media(dummy: str=None) -> str:
    """Open Instagram in the default web browser for chat/browse recommendation."""
    try:
        # 'start chrome' specifically opens in Chrome, 'start' opens in default browser
        os.system('start chrome https://www.instagram.com')
        return "Instagram opened in browser."
    except Exception as e:
        return f"Failed to open Instagram in browser: {e}"

@tool
def play_youtube_content(query_or_url: str = "relaxing music") -> str:
    """
    Open YouTube with a specific search query or direct video URL.
    Provide a search term (e.g., 'meditation music') or a full YouTube URL.
    Defaults to 'relaxing music' if no argument is provided.
    """
    try:
        if query_or_url.startswith("http://") or query_or_url.startswith("https://"):
            url = query_or_url
            return_message = f"YouTube opened to the provided URL: {url}"
        else:
            # Properly encode the search query for YouTube
            encoded_query = urllib.parse.quote_plus(query_or_url)
            # Standard Youtube URL
            url = f"https://www.youtube.com/results?search_query={encoded_query}"
            return_message = f"YouTube opened with search results for: '{query_or_url}'"
        
        # Use 'start chrome' to explicitly open in Chrome, or 'start' for default browser
        subprocess.Popen(['start', 'chrome', url], shell=True)
        return return_message
    except Exception as e:
        return f"Failed to open YouTube: {e}"

@tool
def write_journal_entry(emotion: str="unknown emotion") -> str:
    """
    Append a journal entry to track user's emotion-related activities.
    Includes the detected emotion in the entry.
    """
    entry_text = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] User was feeling {emotion}. Suggested journaling.\n"
    try:
        # Ensure 'journal.txt' is written to the correct directory (e.g., project root)
        # os.getcwd() gets the current working directory from where the script is run
        journal_path = os.path.join(os.getcwd(), "journal.txt")
        with open(journal_path, "a") as f:
            f.write(entry_text)
        return f"Added journal entry to {journal_path}."
    except Exception as e:
        return f"Failed to write journal entry: {e}"

# List of all available tools
tools = [open_spotify, open_social_media, play_youtube_content, write_journal_entry]