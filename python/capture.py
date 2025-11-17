import cv2
import os
import time

# --- Configuration ---
# IMPORTANT: Change this to the folder you want to save images to!
#
# Example for training 12mm sockets:
# SAVE_DIRECTORY = "../dataset/train/12mm" 
#
# Example for validating 15mm sockets:
SAVE_DIRECTORY = "../dataset/validation/15mm" 
# ---------------------

# 1. Create the save directory if it doesn't exist
os.makedirs(SAVE_DIRECTORY, exist_ok=True)
print(f"Saving images to: {os.path.abspath(SAVE_DIRECTORY)}")

# 2. Initialize the webcam
cap = cv2.VideoCapture(0) # 0 is usually the default webcam

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

print("\n--- Webcam Live ---")
print("Press [SPACEBAR] to capture an image.")
print("Press [Q] to quit.")

img_counter = 0

while True:
    # 3. Read a frame from the webcam
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame from webcam.")
        break

    # 4. Display the frame (so you can see what you're capturing)
    cv2.imshow('Press [SPACE] to Capture, [Q] to Quit', frame)

    # 5. Wait for a key press
    key = cv2.waitKey(1) & 0xFF

    # 6. Check for capture key (SPACEBAR)
    if key == 32: # 32 is the ASCII code for spacebar
        # 7. Create a unique filename using a timestamp
        img_name = f"socket_{int(time.time())}.jpg"
        save_path = os.path.join(SAVE_DIRECTORY, img_name)
        
        # 8. Save the current frame to the file
        cv2.imwrite(save_path, frame)
        
        img_counter += 1
        print(f"Image {img_counter} saved: {save_path}")
        
    # 9. Check for quit key (Q)
    elif key == ord('q'):
        print(f"Quitting. Captured {img_counter} images.")
        break

# 10. Clean up and release the resources
cap.release()
cv2.destroyAllWindows()