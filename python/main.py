import cv2
import numpy as np
import time
import json
import serial
import threading
import os
import subprocess
from dotenv import load_dotenv
from google import genai
# Use TFLite Runtime (Lightweight, no Bus Error)
import tflite_runtime.interpreter as tflite

# --- Load Environment Variables (.env) ---
load_dotenv()

# --- Configuration ---
# 1. Initialize Gemini Client
client = genai.Client()

# 2. Load JSON Config
# We use absolute path to avoid "File not found" errors
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, '..', 'config.json')

with open(config_path, 'r') as f:
    config = json.load(f)

MODEL_PATH = os.path.join(script_dir, '..', config['model_path']) # Ensure path is absolute
IMG_SIZE = tuple(config['image_size'])
CLASS_NAMES = config['class_names']
GRID_MAP = config['socket_to_grid_map']
VOICE_MAP = {k: v['servo_id'] for k, v in GRID_MAP.items()}

# System Settings
ARDUINO_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 9600
COOLDOWN_PERIOD = 3.0

# --- MOTION DETECTION SETTINGS (ROI) ---
# Only look for motion in this center box to ignore the gear teeth
CROP_SIZE = 80      # Size of the square box (pixels)
MIN_CROP_AREA = 200  # Smaller threshold because we are looking at a small box

# --- 1. Load TFLite Model ---
print(f"Loading TFLite Model: {MODEL_PATH}")
try:
    interpreter = tflite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    print("✅ Model Loaded Successfully (Lite Mode)")
except Exception as e:
    print(f"FATAL ERROR: Could not load model. {e}")
    exit()

# --- 2. Connect to Arduino ---
try:
    print(f"Connecting to Arduino on {ARDUINO_PORT}...")
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2)
    time.sleep(2) 
    ser.reset_input_buffer()
    ser.write("START\n".encode('utf-8'))
    if "Handshake OK" in ser.readline().decode('utf-8'):
        print("✅ Arduino Handshake Successful.")
    else:
        print("❌ Arduino Handshake Failed. (Check sketch upload)")
        exit()
except Exception as e:
    print(f"FATAL ERROR: Arduino connection failed. {e}")
    exit()

# --- Helper Functions ---

def preprocess_frame(frame):
    img_resized = cv2.resize(frame, IMG_SIZE)
    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    # TFLite expects FLOAT32 input, normalized 0-1
    img_array = (img_rgb / 255.0).astype(np.float32)
    return np.expand_dims(img_array, axis=0)

def record_audio_file(filename="command.wav", duration=3):
    print(f"🎤 Recording for {duration} seconds...")
    # -f cd = 16 bit little endian, 44100Hz stereo
    cmd = f"arecord -d {duration} -f cd -t wav -r 16000 -c 1 {filename}"
    subprocess.call(cmd, shell=True)
    print("🎤 Recording complete.")
    return filename

def process_voice_with_gemini(audio_file):
    print("🤖 Processing with Gemini...")
    try:
        myfile = client.files.upload(file=audio_file)
        map_str = json.dumps(VOICE_MAP)
        prompt = f"""
        Listen to this command. User wants to RELEASE a socket.
        Map: {map_str}
        Return JSON: {{"command": "OPEN", "id": <int>}} or {{"command": "NONE"}}
        """
        # Using 1.5-flash for speed
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=[prompt, myfile])
        
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(clean_text)
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None

# --- Voice Thread (Background) ---
def voice_listener_loop():
    while True:
        # Simple blocking input to avoid spamming Gemini
        input("\n📢 Press [ENTER] to speak command...\n")
        
        wav_file = record_audio_file()
        response = process_voice_with_gemini(wav_file)
        
        if response and response.get("command") == "OPEN":
            servo_id = response["id"]
            print(f"✅ Gemini: Release Servo {servo_id}")
            if ser: ser.write(f"OPEN:{servo_id}\n".encode('utf-8'))
        else:
            print("❌ Gemini didn't understand.")

# Start Voice Thread
t = threading.Thread(target=voice_listener_loop, daemon=True)
t.start()

# --- Main Vision Loop ---
cap = cv2.VideoCapture(0)
if not cap.isOpened(): exit()

# Camera Warmup
print("📷 Warming up camera...")
time.sleep(3)

# 1. Capture Initial Background
ret, bg_frame = cap.read()
if not ret:
    print("Error reading camera.")
    exit()

# 2. Calculate Center Crop Coordinates (ROI)
# We assume 640x480 resolution. Center is (320, 240)
height, width, _ = bg_frame.shape
center_x, center_y = width // 2, height // 2
half_crop = CROP_SIZE // 2

x1 = center_x - half_crop
x2 = center_x + half_crop
y1 = center_y - half_crop
y2 = center_y + half_crop

print(f"📷 ROI Set: x[{x1}:{x2}], y[{y1}:{y2}]")

# 3. Process Background (ROI ONLY)
bg_roi = bg_frame[y1:y2, x1:x2] # Crop first
bg_gray = cv2.cvtColor(bg_roi, cv2.COLOR_BGR2GRAY)
bg_gray = cv2.GaussianBlur(bg_gray, (21, 21), 0)

print("📷 Vision System Active. Ready.")

try:
    last_pred = 0
    while True:
        ret, frame = cap.read()
        if not ret: break

        if time.time() - last_pred > COOLDOWN_PERIOD:
            # --- ROI MOTION DETECTION ---
            # 1. Crop the current frame to match background
            roi = frame[y1:y2, x1:x2]
            
            # 2. Convert crop to gray and blur
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            # 3. Background Subtraction on the CROP
            diff = cv2.absdiff(bg_gray, gray)
            thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
            cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for c in cnts:
                # Ignore tiny noise
                if cv2.contourArea(c) < MIN_CROP_AREA: continue

                print("📷 Center Motion detected! Classifying...")
                
                # --- CLASSIFICATION (Uses FULL FRAME) ---
                # We detect on crop, but classify the whole image
                p_frame = preprocess_frame(frame)
                
                # TFLite Inference
                interpreter.set_tensor(input_details[0]['index'], p_frame)
                interpreter.invoke()
                preds = interpreter.get_tensor(output_details[0]['index'])
                
                idx = np.argmax(preds, axis=1)[0]
                conf = np.max(preds) * 100
                cls = CLASS_NAMES[idx]

                if conf > 80.0: 
                    if cls in GRID_MAP:
                        info = GRID_MAP[cls]
                        angle = info['stepper1_angle']
                        grid = info['grid_id']
                        
                        # Send Command
                        if ser: ser.write(f"SORT:{angle}\n".encode('utf-8'))
                        print(f"✅ Vision: {cls} ({conf:.1f}%) -> {grid}")
                        
                        # --- CRITICAL: RESET BACKGROUND ---
                        # The gear moved, so the old background is garbage.
                        # Wait for robot to finish (approx 5s), then retake background.
                        print("⏳ Sorting... Pausing vision for 5s...")
                        time.sleep(5)
                        
                        # Flush buffer (clear old frames)
                        for _ in range(5): cap.read()
                        
                        # Retake Background
                        ret, new_bg = cap.read()
                        roi_new = new_bg[y1:y2, x1:x2]
                        bg_gray = cv2.cvtColor(roi_new, cv2.COLOR_BGR2GRAY)
                        bg_gray = cv2.GaussianBlur(bg_gray, (21, 21), 0)
                        print("🔄 Background Reset.")
                    else:
                        print(f"⚠️ Config Error: {cls} not in map")
                else:
                    print(f"⚠️ Low confidence: {cls} ({conf:.1f}%)")
                
                last_pred = time.time()
                break
except KeyboardInterrupt:
    print("\nShutting down...")
finally:
    cap.release()
    if ser: ser.close()