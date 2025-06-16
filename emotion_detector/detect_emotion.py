# import cv2
# import numpy as np
# import tensorflow as tf
# import time
# from collections import Counter

# print(tf.__version__)

# model = tf.keras.models.load_model(
#     r'F:\Academic\7th semester\FYP\recommondation_agents_implementation\emotion_detector\best_new.pt'
# )

# label_map = {
#     0: "angry",
#     1: "disgust",
#     2: "fear",
#     3: "happy",
#     4: "sad",
#     5: "surprise",
#     6: "neutral"
# }

# def preprocess_video_for_prediction():
#     cap = cv2.VideoCapture(0)
#     frames = []
#     print("Collecting 30 frames...")

#     while len(frames) < 30:
#         ret, frame = cap.read()
#         if not ret:
#             break

#         frame = cv2.resize(frame, (64, 64))
        
#         # Ensure the frame has 3 channels (convert to RGB if needed)
#         if len(frame.shape) == 2 or frame.shape[2] == 1:
#             frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
#         else:
#             frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
#         frames.append(frame)

#     cap.release()

#     frames = np.array(frames).astype("float32") / 255.0  # Normalize
#     frames = np.expand_dims(frames, axis=0)  # Shape: (1, 30, 64, 64, 3)
#     return frames

# def get_dominant_emotion(duration=60):
#     start_time = time.time()
#     emotions = []

#     while time.time() - start_time < duration:
#         frames = preprocess_video_for_prediction()
#         preds = model.predict(frames)
#         label_index = np.argmax(preds)
#         emotions.append(label_map[label_index])
#         print(f"Detected: {label_map[label_index]}")

#     dominant_emotion = Counter(emotions).most_common(1)[0][0]
#     return dominant_emotion



#pytorch approach
import cv2
import numpy as np
import torch
import time
from collections import Counter
from ultralytics import YOLO

# Load your custom trained YOLO+CNN classification model (.pt)
model_path = r'F:\Academic\7th semester\FYP\recommondation_agents_implementation\emotion_detector\best_new.pt'
model = YOLO(model_path)  # This loads both model structure and weights

label_map = {
    0: "angry",
    1: "boring",
    2: "disgust",
    3: "fear",
    4: "happy",
    5: "neutral",
    6: "sad",
    7: "stress",
    8: "surprise"
}

def preprocess_frame(frame):
    """
    Preprocess the webcam frame to the input size your model expects.
    Usually, YOLOv8 classification models expect 64x64 RGB images.
    """
    img_resized = cv2.resize(frame, (64, 64))
    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    return img_rgb

def get_dominant_emotion(duration=10):
    """
    Capture webcam video for `duration` seconds, predict emotion on each frame,
    then return the most frequent detected emotion.
    """
    cap = cv2.VideoCapture(0)
    start_time = time.time()
    emotions = []

    print(f"Monitoring user for dominant emotion over {duration} seconds...")

    while time.time() - start_time < duration:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        
        # Preprocess frame for model input
        img = preprocess_frame(frame)

        # YOLOv8 model expects input as numpy array, no batch dimension needed
        results = model.predict(img, verbose=False)

        # Get the classification probabilities from results
        probs = results[0].probs  # Probs object from ultralytics

        if probs is None:
            print("No prediction probabilities returned, skipping frame")
            continue

        # Get predicted class index using Probs.top1 property
        pred_idx = probs.top1
        emotion = label_map.get(pred_idx, "unknown")
        emotions.append(emotion)

        print(f"Detected: {emotion}")

        # Small delay to avoid high CPU load and allow frame refresh
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # Return the most frequent detected emotion
    dominant_emotion = Counter(emotions).most_common(1)[0][0] if emotions else "unknown"
    return dominant_emotion
