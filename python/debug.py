# debug_crash.py
print("1. Starting script...")

import os
print("2. Importing OpenCV...")
import cv2
print("3. OpenCV imported.")

print("4. Importing TensorFlow...")
import tensorflow as tf
print("5. TensorFlow imported.")

MODEL_PATH = '../models/socket_classifier_v1.h5'

print(f"6. Checking file existence: {MODEL_PATH}")
if os.path.exists(MODEL_PATH):
    size = os.path.getsize(MODEL_PATH)
    print(f"   File found. Size: {size / (1024*1024):.2f} MB")
else:
    print("   FILE NOT FOUND!")
    exit()

print("7. Attempting to load model...")
try:
    # Turn off GPU for a moment to simplify loading
    with tf.device('/CPU:0'):
        model = tf.keras.models.load_model(MODEL_PATH)
    print("8. SUCCESS! Model loaded.")
except Exception as e:
    print(f"8. FAILED with Python Error: {e}")