import os
import subprocess
import webbrowser

known_apps_list = [
    {"name": "Telegram Desktop", "location": r"C:\Users\Nuwani\Desktop\Telegram.exe"},
    {"name": "Discord", "location": r"C:\Users\Nuwani\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Discord Inc\Discord.lnk"},
    {"name": "zoom", "location": r"C:\Users\Nuwani\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Zoom\Zoom Workplace.lnk"},
]

def open_recommendation(recommendation: dict) -> str:
    print(f"[Open_recommendation] {recommendation}")
    url = recommendation.get("app_url", "")
    app_name = recommendation.get("app_name", "")
    app_name_lower = app_name.lower()

    for app_info in known_apps_list:
        # Check for a match (case-insensitive, allows partial for longer names)
        if app_name_lower == app_info["name"].lower() or \
           (app_name_lower in app_info["name"].lower() and len(app_name_lower) > 2):
            
            app_path_to_use = app_info["location"]

            if not app_path_to_use:
                return f"Error: No path provided for {app_info['name']} in the list."

            # Attempt to launch the app using the provided path
            try:
                if os.path.isdir(app_path_to_use):
                    subprocess.Popen(f'start "" "{app_path_to_use}"', shell=True)
                    return f"Opened folder for {app_info['name']}: {app_path_to_use}. (App might not launch directly from folder path)"
                
                subprocess.Popen(f'"{app_path_to_use}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Successfully launched {app_info['name']} using path: {app_path_to_use}."
            except Exception as e:
                return f"Error launching {app_info['name']} from {app_path_to_use}: {e}"

    if url.startswith("http://") or url.startswith("https://"):
        try:
            # Add search query if present
            if recommendation.get("search_query"):
                search = recommendation["search_query"].replace(" ", "+")
                url += f"/results?search_query={search}"
            webbrowser.open(url)
            return f"Opened {url} in your default web browser."
        except Exception as e:
            return f"Failed to open URL '{url}': {e}"

    # If the recommendation is not a URL and not found in the hardcoded app list
    return f"Recommendation '{recommendation}' is neither a recognized URL nor a known application in the list."
