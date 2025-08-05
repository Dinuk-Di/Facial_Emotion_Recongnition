from flask import Flask, request, jsonify
from flask_cors import CORS
from database.database import init_db, save_UserData, get_user_by_username
from old_utils.state import AppState
import time, threading
from main import start_app

app = Flask(__name__)
CORS(app)

database = {
    "state": {
        "system_status": "Operational",
        "emotion_state": "Neutral",
        "last_response_time": "18 mins ago",
    },
    "recent_records": {
        "recommendation": "Relaxing music",
        "action": "Youtube"
    },
    "apps": [
        {
            "name": "Spotify",
            "icon": "https://example.com/spotify-icon.png",
            "path": "https://www.spotify.com",
            "description": "Music streaming service",
            "type": "entertainment",
            "mode": "online",
            "isAccessGiven": True,
            "isAvailable": True,
        },
        {
            "name": "Youtube",
            "icon": "https://example.com/youtube-icon.png",
            "path": "https://www.youtube.com",
            "description": "Video streaming service",
            "type": "entertainment",
            "mode": "online",
            "isAccessGiven": True,
            "isAvailable": True,
        },
        {
            "name": "Discord",
            "icon": "https://example.com/discord-icon.png",
            "path": "https://www.discord.com",
            "description": "Voice, video, and text communication service",
            "type": "communication",
            "mode": "online",
            "isAccessGiven": False,
            "isAvailable": True,
        }
    ],
    "recommendation": [
        {
            "recommendation": "Relaxing music",
            "apps": [
                {
                    "app": "Youtube",
                    "iconPath": "/com/example/emoify_javafx/icons/youtube.png"
                },
                {
                    "app": "Spotify",
                    "iconPath": "/com/example/emoify_javafx/icons/Spotify.png"
                },
                {
                    "app": "Discord",
                    "iconPath": "/com/example/emoify_javafx/icons/Discord.png"
                }
            ],
        },
        {
            "recommendation": "Play games",
            "apps": [
                {
                    "app": "Solitaire",
                    "iconPath": "/com/example/emoify_javafx/icons/Solitaire.png"
                },
                {
                    "app": "Delta Force",
                    "iconPath": "/com/example/emoify_javafx/icons/Delta_Force.png"
                },
                {
                    "app": "Breathedge",
                    "iconPath": "/com/example/emoify_javafx/icons/Breathedge.png"
                }
            ],
        },
        {
            "recommendation": "Watch movies",
            "apps": [
                {
                    "app": "Movie Player",
                    "iconPath": "/com/example/emoify_javafx/icons/default_app.png"
                },
                {
                    "app": "Movie Player 2",
                    "iconPath": "/com/example/emoify_javafx/icons/default_app.png"
                },
                {
                    "app": "Movie Player 3",
                    "iconPath": "/com/example/emoify_javafx/icons/default_app.png"
                }
            ],
        }
    ],
    "showRecommendation": {
        "show": True
    },
    "selectedApp": {
        "name": "Spotify"
    }
}

@app.route('/')
def home():
    return "Hello, Flask!"

@app.route('/api/saveUserData', methods=['POST'])
def save_user_data():
    data = request.json
    userName = data.get('userName')
    password = data.get('password')
    phoneNumber = data.get('phoneNumber')

    if not all([userName, password, phoneNumber]):
        return jsonify({"error": "Missing required fields"}), 400

    save_UserData(userName, password, phoneNumber)
    return jsonify({"message": "User data saved successfully"}), 201

@app.route('/api/getUserData', methods=['GET'])
def get_user_data():
    userName = request.args.get('userName')
    if not userName:
        return jsonify({"error": "userName parameter is required"}), 400
    
    user = get_user_by_username(userName)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"userName": user[0], "phoneNumber": user[2]}), 200

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(database["state"])

@app.route('/api/recentRecords', methods=['GET'])
def get_recent_records():
    
    return jsonify(database["recent_records"])

@app.route('/api/apps', methods=['GET'])
def get_apps():
    return jsonify(database["apps"])

@app.route('/api/recommendation', methods=['GET'])
def get_recommendation():
    return jsonify(database["recommendation"])

@app.route('/api/showRecommendation', methods=['GET'])
def get_show_recommendation():
    return jsonify(database["showRecommendation"])

@app.route('/api/setShowRecommendation', methods=['POST'])
def set_show_recommendation():
    data = request.json
    show_recommendation = data.get('showRecommendation')
    if show_recommendation is not None:
        database["showRecommendation"]["show"] = show_recommendation
        return jsonify({"message": "Show recommendation updated successfully"}), 200
    return jsonify({"error": "Invalid data"}), 400

@app.route('/api/setSelectedApp', methods=['POST'])
def set_selected_app():
    data = request.json
    selected_app = data.get('selectedApp')
    if selected_app is not None:
        database["selectedApp"]["name"] = selected_app
        return jsonify({"message": "Selected app updated successfully"}), 200
    return jsonify({"error": "Invalid data"}), 400

@app.route('/api/getExecutedState', methods=['GET'])
def get_executed_state():
    return jsonify({"executed": get_execution_state()})

def start_flask():
    app.run(debug=True, port=5000)

def initialize_app():
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    start_app()

def get_execution_state():
    return AppState.get_executed()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
