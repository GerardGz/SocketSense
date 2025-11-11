import cv2
import tensorflow as tf
import numpy as np
import time
import json

# --- Configuration ---
MODEL_PATH = '../models/socket_classifier_v1.h5'
IMG_SIZE = (224, 224)

# --- Trigger Settings ---
MIN_CONTOUR_AREA = 2000  # The minimum size of motion to consider it an "object"
COOLDOWN_PERIOD = 3.0    # Wait 3 seconds after a prediction before triggering again

# --- 1. Load the Trained Model (Do this only ONCE) ---
print("Loading model...")
model = tf.keras.models.load_model(MODEL_PATH)
print("Model loaded successfully!")

with open('../config.json', 'r') as f:
    config = json.load(f)
CLASS_NAMES = config['class_names']
GRID_MAP = config['socket_to_grid_map']

# --- 2. Function to Preprocess a Live Camera Frame ---
def preprocess_frame(frame):
    """Prepares a raw camera frame for the model."""
    img_resized = cv2.resize(frame, IMG_SIZE)
    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    img_array = img_rgb / 255.0
    img_batch = np.expand_dims(img_array, axis=0)
    return img_batch

# --- 3. Main Loop for Triggered Prediction ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print("Camera started. Looking for an empty background...")
time.sleep(2) # Give camera time to adjust

# Capture the initial background frame
ret, background_frame = cap.read()
if not ret:
    print("Error: Could not capture initial frame.")
    exit()
    
# Helps with motion detection
background_gray = cv2.cvtColor(background_frame, cv2.COLOR_BGR2GRAY)
background_gray = cv2.GaussianBlur(background_gray, (21, 21), 0)
print("Background captured. Ready for detection.")

last_prediction_time = 0
current_prediction = "None"

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Only check for motion if we are not in the cooldown period
    if time.time() - last_prediction_time > COOLDOWN_PERIOD:
        current_prediction = "None" # Reset prediction after cooldown

        # --- Motion Detection Logic ---
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # Compute the difference between the background and current frame
        frame_delta = cv2.absdiff(background_gray, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        
        # Find contours of the detected motion
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # If the contour is too small, ignore it
            if cv2.contourArea(contour) < MIN_CONTOUR_AREA:
                continue

            print("Motion detected. Running classification...")
            
            # Prepare the frame and predict
            processed_frame = preprocess_frame(frame)
            predictions = model.predict(processed_frame) # [0.3, 0.8, 0.3, 1.0]
            
            # Get the result
            predicted_class_idx = np.argmax(predictions, axis=1)[0]
            confidence = np.max(predictions) * 100
            predicted_class = CLASS_NAMES[predicted_class_idx]

            if predicted_class in GRID_MAP:
                # figure out how many degrees to rotate
                action = GRID_MAP[predicted_class]
                angle_to_rotate = action['rotation_angle']
                grid_name = action['grid_id']
    
                # c++ will read this to know what to rotate
                command_string = f"ROTATE:{angle_to_rotate}"
    
                # Send the command by printing to standard output
                print(command_string, flush=True)
    
                print(f"Action: Detected {predicted_class} ({confidence:.2f}%), sending to {grid_name}. Command: {command_string}")
            else:
                print(f"Error: {predicted_class} not found in config map.")
            
            # Update the cooldown timer and break the loop to show the result
            last_prediction_time = time.time()
            break # Only classify the first large motion detected

# Cleanup
cap.release()
cv2.destroyAllWindows()