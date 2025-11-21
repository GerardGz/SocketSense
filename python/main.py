# We clone this file inside the pi terminal and install dependencies
# then we can just do python3 main.py
import cv2
import tensorflow as tf
import numpy as np
import time
import json
import serial
import speech_recognition as sr
import threading

# --- Configuration ---
MODEL_PATH = '../models/socket_classifier_v1.h5'
IMG_SIZE = (224, 224)

ARDUINO_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 9600

MIN_CONTOUR_AREA = 2000
COOLDOWN_PERIOD = 3.0

# --- 1. Load the Trained Model ---
print("Loading model...")
model = tf.keras.models.load_model(MODEL_PATH)
print("Model loaded successfully!")

# --- 2. Connect to Arduino ---
try:
    print(f"Connecting to Arduino on {ARDUINO_PORT}...")
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2)
    time.sleep(2) 
    ser.reset_input_buffer()
    print("Sending 'START' handshake...")
    ser.write("START\n".encode('utf-8'))
    response = ser.readline().decode('utf-8').strip()
    if "Handshake OK" in response:
        print(f"Arduino replied: {response} --- Handshake successful. ---")
    else:
        print(f"Handshake FAILED. Arduino sent: {response}")
        ser.close()
        exit()
except serial.SerialException as e:
    print(f"FATAL ERROR: Could not open port {ARDUINO_PORT}. {e}")
    exit()

# --- 3. Load Config ---
with open('../config.json', 'r') as f:
    config = json.load(f)
CLASS_NAMES = config['class_names']
GRID_MAP = config['socket_to_grid_map']

# --- 4. Preprocess function ---
def preprocess_frame(frame):
    img_resized = cv2.resize(frame, IMG_SIZE)
    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    img_array = img_rgb / 255.0
    img_batch = np.expand_dims(img_array, axis=0)
    return img_batch

# --- 5. Voice Command Mapping ---
SIZE_TO_HATCH = {
    10: "OPEN:1",
    12: "OPEN:9",
    13: "OPEN:5",
    15: "OPEN:13"
}

def parse_voice_command(text):
    text = text.lower()
    if "release" in text:
        for size in ["10", "12", "13", "15"]:
            if size in text:
                return SIZE_TO_HATCH[int(size)]
    return None

# --- 6. Setup Speech Recognition ---
recognizer = sr.Recognizer()
try:
    mic = sr.Microphone()
    print("Microphone ready for voice commands.")
except Exception as e:
    print(f"Microphone error: {e}")
    mic = None

# --- 7. Initialize Camera ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    ser.close()
    exit()

time.sleep(2)
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

# --- 8. Voice Recognition Thread ---
def voice_thread():
    if mic is None:
        return
    while True:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=0.5, phrase_time_limit=3)
            try:
                text = recognizer.recognize_google(audio)
                print(f"Voice command detected: {text}")
                Open_Command = parse_voice_command(text)
                if Open_Command and ser:
                    ser.write(f"{Open_Command}\n".encode('utf-8'))
                    print(f"Sent command to Arduino to open {Open_Command}.")
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print(f"Speech recognition error: {e}")
        except sr.WaitTimeoutError:
            continue

# Start voice recognition in a daemon thread
t = threading.Thread(target=voice_thread, daemon=True)
t.start()

# --- 9. Main Loop (Motion Detection & Classification) ---
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Dropped frame.")
            break

        if time.time() - last_prediction_time > COOLDOWN_PERIOD:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            frame_delta = cv2.absdiff(background_gray, gray)
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                if cv2.contourArea(contour) < MIN_CONTOUR_AREA:
                    continue

                print("Motion detected. Running classification...")
                processed_frame = preprocess_frame(frame)
                predictions = model.predict(processed_frame)
                predicted_class_idx = np.argmax(predictions, axis=1)[0]
                confidence = np.max(predictions) * 100
                predicted_class = CLASS_NAMES[predicted_class_idx]

                if confidence > 70.0: # Only act if 70% sure
                    if predicted_class in GRID_MAP:
                        action_info = GRID_MAP[predicted_class]
                        angle_to_rotate = action_info['stepper1_angle']
                        grid_name = action_info['grid_id']
                        
                        command_string = f"SORT:{angle_to_rotate}\n"
                        ser.write(command_string.encode('utf-8'))
                        
                        print(f"Action: Detected {predicted_class} ({confidence:.2f}%), sent to {grid_name}")
                    else:
                        print(f"Error: {predicted_class} not found in config map.")
                else:
                    print(f"Ignored: Detection too weak ({predicted_class} at {confidence:.2f}%)")

                last_prediction_time = time.time()
                break

except KeyboardInterrupt:
    print("\nShutting down by user command...")

finally:
    print("Releasing resources...")
    cap.release()
    ser.close()
    print("Camera and Serial port released")
