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
# --- NEW: Import TFLite Runtime ---
import tflite_runtime.interpreter as tflite

load_dotenv()

# --- Configuration ---
client = genai.Client()

# Load Config
with open('../config.json', 'r') as f:
    config = json.load(f)

# Make sure config points to the .tflite file now!
MODEL_PATH = config['model_path'] 
IMG_SIZE = tuple(config['image_size'])
CLASS_NAMES = config['class_names']
GRID_MAP = config['socket_to_grid_map']
VOICE_MAP = {k: v['servo_id'] for k, v in GRID_MAP.items()}

ARDUINO_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 9600
MIN_CONTOUR_AREA = 5000
COOLDOWN_PERIOD = 3.0

# --- 1. Load TFLite Model ---
print(f"Loading TFLite Model: {MODEL_PATH}")
# We use the Interpreter, not Keras
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

# Get input/output details so we know how to pass data in
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
print("✅ Model Loaded Successfully (Lite Mode)")

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
        print("❌ Arduino Handshake Failed.")
        exit()
except Exception as e:
    print(f"FATAL ERROR: Arduino connection failed. {e}")
    exit()

# --- Helper Functions ---

def preprocess_frame(frame):
    img_resized = cv2.resize(frame, IMG_SIZE)
    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    # TFLite expects FLOAT32 input, usually normalized 0-1
    img_array = (img_rgb / 255.0).astype(np.float32)
    return np.expand_dims(img_array, axis=0)

def record_audio_file(filename="command.wav", duration=3):
    print(f"🎤 Recording for {duration} seconds...")
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
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=[prompt, myfile])
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(clean_text)
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None

def voice_listener_loop():
    while True:
        input("\n📢 Press [ENTER] to speak...\n")
        wav_file = record_audio_file()
        response = process_voice_with_gemini(wav_file)
        if response and response.get("command") == "OPEN":
            servo_id = response["id"]
            print(f"✅ Gemini: Release Servo {servo_id}")
            if ser: ser.write(f"OPEN:{servo_id}\n".encode('utf-8'))
        else:
            print("❌ Gemini didn't understand.")

t = threading.Thread(target=voice_listener_loop, daemon=True)
t.start()

# --- Main Vision Loop ---
cap = cv2.VideoCapture(0)
if not cap.isOpened(): exit()

time.sleep(10)
ret, bg_frame = cap.read()
# Fix: Blur the grayscale image
bg_gray = cv2.cvtColor(bg_frame, cv2.COLOR_BGR2GRAY)
bg_gray = cv2.GaussianBlur(bg_gray, (21, 21), 0)

print("📷 Vision System Active.")

try:
    last_pred = 0
    while True:
        ret, frame = cap.read()
        if not ret: break

        if time.time() - last_pred > COOLDOWN_PERIOD:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            diff = cv2.absdiff(bg_gray, gray)
            thresh = cv2.threshold(diff, 50, 255, cv2.THRESH_BINARY)[1]
            cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for c in cnts:
                if cv2.contourArea(c) < MIN_CONTOUR_AREA: continue

                print("📷 Motion detected...")
                p_frame = preprocess_frame(frame)
                
                # --- TFLite Inference Block ---
                # 1. Set the input data
                interpreter.set_tensor(input_details[0]['index'], p_frame)
                
                # 2. Run the model
                interpreter.invoke()
                
                # 3. Get the output data
                preds = interpreter.get_tensor(output_details[0]['index'])
                # ------------------------------

                idx = np.argmax(preds, axis=1)[0]
                conf = np.max(preds) * 100
                cls = CLASS_NAMES[idx]

                if conf > 70.0 and cls in GRID_MAP:
                    info = GRID_MAP[cls]
                    angle = info['stepper1_angle']
                    
                    # 1. Send Command
                    print(f"✅ Vision: Detected {cls}. Sorting...")
                    if ser: ser.write(f"SORT:{angle}\n".encode('utf-8'))
                    
                    # 2. PAUSE Python to let the robot finish physically
                    # (Adjust this time to match your physical sort time)
                    time.sleep(5) 
                    
                    # 3. FLUSH the camera buffer
                    # The camera buffer still has 5 seconds of "old" frames in it.
                    # We need to grab a few dummy frames to get to the "now".
                    for _ in range(5):
                        cap.read()
                        
                    # 4. RETAKE the Background
                    # Now that the robot is done and gone, this is the new "empty" state.
                    ret, bg_frame = cap.read()
                    gray_bg = cv2.cvtColor(bg_frame, cv2.COLOR_BGR2GRAY)
                    background_gray = cv2.GaussianBlur(gray_bg, (21, 21), 0)
                    
                    print("🔄 Background reset. Ready for next socket.")
                    
                    # Reset timer so we don't trigger immediately
                    last_pred = time.time()
                    break
except KeyboardInterrupt:
    print("\nShutting down...")
finally:
    cap.release()
    if ser: ser.close()