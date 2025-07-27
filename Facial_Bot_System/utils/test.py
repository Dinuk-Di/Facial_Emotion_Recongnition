# ### main window testing
# from runner_interface import launch_window
# import sys

# # def setup_Icons(app_name, icon_paths):

# #     default_icon = "res/default_app.png"
# #     icon_path = default_icon
    
# #     for idx, icon in enumerate(icon_paths):
# #         if app_name == icon['app_name']:
# #             icon_path = icon['icon_path']
# #             break

# #     return icon_path

# if __name__ == "__main__":

#     # Icons_paths = [
#     #     {"app_name": "YouTube","icon_path": "res/youtube_resize.png"},
#     #     {"app_name": "Spotify","icon_path": "res/Spotify.png"},
#     #     {"app_name": "Discord","icon_path": "res/Discord.png"},
#     #     {"app_name": "Default","icon_path": "res/default_app.png"},
#     # ]

#     options = [
#         {"app_name": "YouTube","text": "watch relaxing video"},
#         {"app_name": "Spotify","text": "listen to relaxing music"},
#         {"app_name": "Discord","text": "talk with friends"},
#         {"app_name": "Mass Effect","text": "play with friends"}
#     ]

#     # for idx, choice in enumerate(options):
#     #     icon = setup_Icons(choice['app_name'], Icons_paths)
#     #     print(f"option: {choice}, choice_id: {idx}, choice_icon: {icon}\n")

#     window, app = launch_window(options=options)

#     choice = int(input("Enter your choice (1-4): "))

#     #if choice == "Show":
#     #    window

#     app.exec()
    
#     print("Final Selected Choice:", window.selectedChoice)



##########################
# import ollama
# import time

# detected_task = "Coding in VS code"
# emotion = "Sad"

# prompt = f"""
# User feels {emotion} while doing {detected_task}. Suggest one mood-improvement action from this list: 
# ["Play music", "Watch funny videos", "Take a break", "Quick game", "Coding Bot", "Nothing"].

# Also, suggest 3 apps (with URLs/search queries) to help. Example:
# - YouTube: "chill lofi music", https://youtube.com
# - Spotify: "relax playlist", https://open.spotify.com
# """
# print("Model running...")

# start_time = time.time()

# ollama.generate(
#     model="qwen3:4b",
#     prompt="ping",  # Minimal prompt
#     options={"temperature": 0, "num_predict": 1}  # Shortest possible response
# )

# response = ollama.generate(
#     model="qwen3:4b",
#     prompt=prompt,
#     options={"temperature": 0.2, "num_gpu": 1}
# )
# elapsed_time = time.time() - start_time

# response_text = response["response"]
# print("Recommendation is done.")
# print("[Agent] Raw LLM Response:", response_text)
# print(f"Time elapsed: {elapsed_time}")

import win32api
import win32con
import subprocess

# win32api.ShellExecute(
#     0,                      # hwnd: handle to parent window (0 for no parent)
#     "open",                 # operation: "open", "print", "edit", "explore", "find"
#     "explorer.exe",         # file: The program to execute (explorer.exe for shell:Appsfolder)
#     r"shell:Appsfolder\SpotifyAB.Spotify_8wekyb3d8bbwe!Spotify",           # parameters: The AUMID as a shell URI
#     None,                   # directory: default directory
#     win32con.SW_SHOWNORMAL  # show command: how the application is shown
# )

output = subprocess.check_output('where paint', shell= True, text = True)
first_path = output.strip().split('\n')[0]
print(f"Path: {first_path}")