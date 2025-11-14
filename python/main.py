# We clone this file inside the pi terminal and install dependencies
# then we can just do python3 main.py
import cv2
import tensorflow as tf
import numpy as np
import time
import json
import serial

# --- Configuration ---
MODEL_PATH = '../models/socket_classifier_v1.h5'
IMG_SIZE = (224, 224)

# run: ls /dev/tty* inside pi terminal to find this:
ARDUINO_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 9600

# --- Trigger Settings ---
MIN_CONTOUR_AREA = 2000
COOLDOWN_PERIOD = 3.0

# --- 1. Load the Trained Model (Do this only ONCE) ---
print("Loading model...")
model = tf.keras.models.load_model(MODEL_PATH)
print("Model loaded successfully!")

try:
    print(f"Connecting to Arduino on {ARDUINO_PORT}...")
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2) # 2-second timeout
    
    # 1. Wait for Arduino to reset
    print("Waiting for Arduino to reboot...")
    time.sleep(2) 
    
    # 2. Clear any "booting..." messages
    ser.reset_input_buffer()
    
    # 3. Send the "START" handshake
    print("Sending 'START' handshake...")
    ser.write("START\n".encode('utf-8'))
    
    # 4. Wait for the "Handshake OK" reply
    response = ser.readline().decode('utf-8').strip()
    
    if "Handshake OK" in response:
        print(f"Arduino replied: {response}")
        print("--- Handshake successful. System is LIVE. ---")
    else:
        print(f"--- Handshake FAILED. ---")
        print(f"Arduino sent an unexpected reply: {response}")
        ser.close()
        exit()
except serial.SerialException as e:
    print(f"\n--- FATAL ERROR ---")
    print(f"Could not open port {ARDUINO_PORT}. {e}")
    print("1. Is the Arduino plugged in?")
    print("2. Is the ARDUINO_PORT variable correct?")
    exit()

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
    ser.close() # Close serial port if camera fails
    exit()

print("Camera started. Looking for an empty background...")
time.sleep(2) # Give camera time to adjust

ret, background_frame = cap.read()
if not ret:
    print("Error: Could not capture initial frame.")
    ser.close()
    cap.release()
    exit()
    
background_gray = cv2.cvtColor(background_frame, cv2.COLOR_BGR2GRAY)
background_gray = cv2.GaussianBlur(background_gray, (21, 21), 0)
print("Background captured. Ready for detection.")

last_prediction_time = 0

# --- NEW: Added try...finally block ---
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Dropped frame.")
            break

        # Only check for motion if we are not in the cooldown period
        if time.time() - last_prediction_time > COOLDOWN_PERIOD:
            # --- Motion Detection Logic ---
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            frame_delta = cv2.absdiff(background_gray, gray)
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                if cv2.contourArea(contour) < MIN_CONTOUR_AREA:
                    continue

                print("Motion detected. Running classification...")
                
                # Prepare the frame and predict
                processed_frame = preprocess_frame(frame)
                predictions = model.predict(processed_frame)
                
                # Get the result
                predicted_class_idx = np.argmax(predictions, axis=1)[0]
                confidence = np.max(predictions) * 100
                predicted_class = CLASS_NAMES[predicted_class_idx]

                if predicted_class in GRID_MAP:
                    action_info = GRID_MAP[predicted_class]
                    angle_to_rotate = action_info['stepper1_angle']
                    grid_name = action_info['grid_id']
        
                    command_string = f"SORT:{angle_to_rotate}\n"  

                    ser.write(command_string.encode('utf-8'))   

                    print(f"Action: Detected {predicted_class} ({confidence:.2f}%), sending to {grid_name}. Command: {command_string.strip()}")
                else:
                    print(f"Error: {predicted_class} not found in config map.")
                
                last_prediction_time = time.time()
                break # Only classify the first large motion detected

except KeyboardInterrupt:
    print("\nShutting down by user command...")

finally:
    print("Releasing resources...")
    cap.release()
    ser.close()
    print("Camera and Serial port released")