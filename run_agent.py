from emotion_agent import recommend_action
from emotion_detector.detect_emotion import get_emotion

emotion = get_emotion()
print(f"Detected Emotion: {emotion}")

recommendation = recommend_action(emotion)
print("Agent Recommendation:", recommendation)