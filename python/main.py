import cv2
import tensorflow as tf
import numpy as np
import time
import json
import serial
import threading
import os
import subprocess
from dotenv import load_dotenv
from google import genai  #

# This looks for a .env file in the project root and loads GEMINI_API_KEY
load_dotenv() 

# Client auto-reads 'GOOGLE_API_KEY' or 'GEMINI_API_KEY' from environment
client = genai.Client()

MODEL_PATH = '../models/socket_classifier_v1.h5'
IMG_SIZE = (224, 224)

ARDUINO_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 9600
MIN_CONTOUR_AREA = 2000
COOLDOWN_PERIOD = 3.0

# --- 1. Load Config & Map Data ---
with open('../config.json', 'r') as f:
    config = json.load(f)

CLASS_NAMES = config['class_names']
GRID_MAP = config['socket_to_grid_map']

# Voice Map for Gemini
VOICE_MAP = {k: v['servo_id'] for k, v in GRID_MAP.items()}

# --- 2. Load our cnn ---
print("Loading Vision Model...")
model = tf.keras.models.load_model(MODEL_PATH)
print("Model loaded!")

# --- 3. Connect to Arduino ---
try:
    print(f"Connecting to Arduino on {ARDUINO_PORT}...")
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2)
    time.sleep(2) 
    ser.reset_input_buffer()
    ser.write("START\n".encode('utf-8'))
    if "Handshake OK" in ser.readline().decode('utf-8'):
        print("Arduino Handshake Successful.")
    else:
        print("Arduino Handshake Failed.")
        exit()
except Exception as e:
    print(f"FATAL ERROR: Arduino connection failed. {e}")
    exit()

# --- Helper Functions ---

def preprocess_frame(frame):
    img_resized = cv2.resize(frame, IMG_SIZE)
    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    img_array = img_rgb / 255.0
    return np.expand_dims(img_array, axis=0)

def record_audio_file(filename="command.wav", duration=3):
    """Records audio using system 'arecord'."""
    print(f"Recording for {duration} seconds...")
    # Force overwrite (-y doesn't exist in arecord, simple open is fine)
    # -f cd is high quality, -c 1 is mono
    cmd = f"arecord -d {duration} -f cd -t wav -r 16000 -c 1 {filename}"
    subprocess.call(cmd, shell=True)
    print("Recording complete.")
    return filename

def process_voice_with_gemini(audio_file):
    """Uploads audio and asks Gemini for JSON."""
    print("🤖 Processing with Gemini...")
    
    try:
        # 1. Upload the file using the Client
        myfile = client.files.upload(file=audio_file)
        
        # 2. Prepare the Prompt
        map_str = json.dumps(VOICE_MAP)
        prompt = f"""
        Listen to this voice command for a socket sorting robot.
        The user wants to RELEASE a specific socket.
        
        Map of Socket Sizes to Servo IDs: {map_str}
        
        Instructions:
        1. Identify the socket size the user wants.
        2. Return ONLY valid JSON. Format: {{"command": "OPEN", "id": <int>}}
        3. If unclear, return: {{"command": "NONE"}}
        """

        # Using 1.5-flash as it is currently the fastest/cheapest for audio
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=[prompt, myfile]
        )
        
        # 4. Clean & Parse
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(clean_text)

    except Exception as e:
        print(f"Gemini Error: {e}")
        return None

# --- Voice Thread ---
def voice_listener_loop():
    while True:
        input("\nPress [ENTER] to speak (e.g. 'Release 12')...\n")
        
        wav_file = record_audio_file()
        response = process_voice_with_gemini(wav_file)
        
        if response and response.get("command") == "OPEN":
            servo_id = response["id"]
            cmd_str = f"OPEN:{servo_id}\n"
            
            print(f"Gemini: Release Servo {servo_id}")
            if ser: ser.write(cmd_str.encode('utf-8'))
        else:
            print("Gemini didn't understand.")

# Start Voice Thread
t = threading.Thread(target=voice_listener_loop, daemon=True)
t.start()

# --- Main Vision Loop ---
cap = cv2.VideoCapture(0)
if not cap.isOpened(): exit()

time.sleep(2)
ret, bg_frame = cap.read()
# Correct background blur logic
bg_gray = cv2.cvtColor(bg_frame, cv2.COLOR_BGR2GRAY)
bg_gray = cv2.GaussianBlur(bg_gray, (21, 21), 0)

print("Vision System Active.")

try:
    last_pred = 0
    while True:
        ret, frame = cap.read()
        if not ret: break

        if time.time() - last_pred > COOLDOWN_PERIOD:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            diff = cv2.absdiff(bg_gray, gray)
            thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
            cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for c in cnts:
                if cv2.contourArea(c) < MIN_CONTOUR_AREA: continue

                print("Motion detected...")
                p_frame = preprocess_frame(frame)
                preds = model.predict(p_frame)
                
                idx = np.argmax(preds, axis=1)[0]
                conf = np.max(preds) * 100
                cls = CLASS_NAMES[idx]

                if conf > 70.0 and cls in GRID_MAP:
                    info = GRID_MAP[cls]
                    angle = info['stepper1_angle']
                    grid = info['grid_id']
                    
                    if ser: ser.write(f"SORT:{angle}\n".encode('utf-8'))
                    print(f"Vision: {cls} ({conf:.1f}%) -> {grid}")
                
                last_pred = time.time()
                break
except KeyboardInterrupt:
    print("\nShutting down...")
finally:
    cap.release()
    if ser: ser.close()