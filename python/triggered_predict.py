# triggered_predict.py

import cv2
import tensorflow as tf
import numpy as np
import time

# --- Configuration ---
MODEL_PATH = '../models/socket_classifier_v1.h5'
IMG_SIZE = (224, 224)
# IMPORTANT: Must be in alphabetical order of your training folders
CLASS_NAMES = ['A1', 'A2', 'B1'] # Example: Change to your actual grid locations

# --- Trigger Settings ---
MIN_CONTOUR_AREA = 2000  # The minimum size of motion to consider it an "object"
COOLDOWN_PERIOD = 3.0    # Wait 3 seconds after a prediction before triggering again

# --- 1. Load the Trained Model (Do this only ONCE) ---
print("Loading model...")
model = tf.keras.models.load_model(MODEL_PATH)
print("Model loaded successfully!")

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

            # --- TRIGGER! ---
            print("Motion detected! Running classification...")
            
            # Prepare the frame and predict
            processed_frame = preprocess_frame(frame)
            predictions = model.predict(processed_frame)
            
            # Get the result
            predicted_class_idx = np.argmax(predictions, axis=1)[0]
            confidence = np.max(predictions) * 100
            predicted_class = CLASS_NAMES[predicted_class_idx]
            current_prediction = f"{predicted_class} ({confidence:.2f}%)"
            
            # Update the cooldown timer and break the loop to show the result
            last_prediction_time = time.time()
            break # Only classify the first large motion detected

    # Display the current prediction on the screen
    cv2.putText(frame, f"Prediction: {current_prediction}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Show the resulting frame
    cv2.imshow('Socket Detector', frame)

    if cv2.waitKey(1) == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()