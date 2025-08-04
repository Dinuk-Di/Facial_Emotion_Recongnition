import customtkinter as ctk
import requests
import os
from dotenv import load_dotenv
import json
from PIL import Image, ImageTk


load_dotenv()

QWEN_API_KEY = os.getenv("QWEN_API_KEY")


# Initial Negative Emotion
initial_emotion = "Stress"
chat_history = []

# Prompt Template
PROMPT_TEMPLATE = """
You are a friendly, empathetic chatbot. Your main goal is to improve the user's mood and make them feel positive.
The user currently feels: {emotion}.
If the user emotion is negative, you will respond with a positive message to help lift their mood.
start a conversation with the user, asking how they are doing and offering support. Like ask them about their day, hobbies, or interests.
Give some jokes or positive affirmations to cheer them up. Also give some motivational quotes or suggestions to help them feel better.
You will always respond in a friendly, positive, and encouraging manner.
Always respond with kindness, optimism, and a conversational tone.
Conversation so far:
{history}
User: {user_input}
Bot:
"""

# HuggingFace Inference API call
def query_huggingface(prompt):
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
                "Authorization": f"Bearer {QWEN_API_KEY}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "qwen/qwen-2.5-72b-instruct:free",
                "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
                ]
            }))
    return response.json()

# Generate chatbot response
def get_chatbot_response(user_input):
    global chat_history

    # Build prompt with conversation history
    history_text = "\n".join(chat_history[-5:])  # Keep last 5 exchanges
    prompt = PROMPT_TEMPLATE.format(emotion=initial_emotion, history=history_text, user_input=user_input)

    # API Request
    result = query_huggingface(prompt)

    # Extract response from OpenRouter structure
    try:
        bot_response = result["choices"][0]["message"]["content"]
        print(f"Bot Response: {bot_response}")
    except (KeyError, IndexError):
        bot_response = "Sorry, I couldn't generate a response right now. Please try again!"

    # Update chat history
    chat_history.append(f"User: {user_input}")
    chat_history.append(f"Bot: {bot_response}")

    return bot_response

# ------------------- UI -------------------
def send_message(event=None):
    user_input = entry.get().strip()
    if user_input == "":
        return

    add_message(user_input, "user")
    entry.delete(0, "end")

    bot_response = get_chatbot_response(user_input)
    add_message(bot_response, "bot")


def add_message(message, sender="bot"):
    # Container Frame
    message_frame = ctk.CTkFrame(chatbox_frame, fg_color="transparent")
    message_frame.pack(fill="x", pady=5, padx=10, anchor="w" if sender == "bot" else "e")

    # Icon
    icon = bot_icon if sender == "bot" else user_icon
    icon_label = ctk.CTkLabel(message_frame, image=icon, text="")
    icon_label.pack(side="left" if sender == "bot" else "right", padx=5)

    # Message Bubble
    bubble_color = "#2A2D32" if sender == "bot" else "#1F6AA5"
    text_label = ctk.CTkLabel(
        message_frame,
        text=message,
        wraplength=300,
        fg_color=bubble_color,
        corner_radius=12,
        justify="left",
        padx=10,
        pady=8
    )
    text_label.pack(side="left" if sender == "bot" else "right")

    # Scroll down
    chatbox_canvas.update_idletasks()
    chatbox_canvas.yview_moveto(1.0)


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Mood Booster Chatbot")
app.geometry("500x650")

# Load icons
user_img = Image.open("assets/res/Skype.png").resize((30, 30))
bot_img = Image.open("assets/res/Icon.jpg").resize((30, 30))
user_icon = ImageTk.PhotoImage(user_img)
bot_icon = ImageTk.PhotoImage(bot_img)

# Main Frame (Chat Area)
main_frame = ctk.CTkFrame(app, fg_color="transparent")
main_frame.pack(fill="both", expand=True)

# Scrollable Chat Area
chatbox_canvas = ctk.CTkCanvas(main_frame, bg="#1E1E1E", highlightthickness=0)
chatbox_canvas.pack(side="left", fill="both", expand=True)

scrollbar = ctk.CTkScrollbar(main_frame, orientation="vertical", command=chatbox_canvas.yview)
scrollbar.pack(side="right", fill="y")

chatbox_frame = ctk.CTkFrame(chatbox_canvas, fg_color="transparent")
chatbox_frame.bind("<Configure>", lambda e: chatbox_canvas.configure(scrollregion=chatbox_canvas.bbox("all")))
chatbox_canvas.create_window((0, 0), window=chatbox_frame, anchor="nw")
chatbox_canvas.configure(yscrollcommand=scrollbar.set)

# Input Area (Pinned to Bottom)
input_frame = ctk.CTkFrame(app, fg_color="#2C2F33")
input_frame.pack(side="bottom", fill="x", pady=10)

entry = ctk.CTkEntry(input_frame, width=360, placeholder_text="Type your message...")
entry.grid(row=0, column=0, padx=10)
entry.bind("<Return>", send_message)

send_btn = ctk.CTkButton(input_frame, text="Send", command=send_message)
send_btn.grid(row=0, column=1)

# Initial Bot Message
add_message("Hi! I heard you're feeling a bit down. Let's chat and make your day better! 😊", "bot")

app.mainloop()