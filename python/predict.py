import tensorflow as tf
import numpy as np
import os
import sys

# --- Configuration ---
MODEL_PATH = '../models/socket_classifier_v1.h5'
IMG_SIZE = (224, 224)
CLASS_NAMES = ['class1', 'class2', 'class3']  # Replace with your actual folder names

# --- 1. Load the Trained Model ---
print(f"Loading model from {MODEL_PATH}...")
model = tf.keras.models.load_model(MODEL_PATH)
print("Model loaded successfully!")

# --- 2. Function to Load and Preprocess a Single Image ---
def load_and_preprocess_image(image_path):
    """Load an image from disk, resize, normalize, and return a batch tensor."""
    img = tf.keras.preprocessing.image.load_img(image_path, target_size=IMG_SIZE)
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = img_array / 255.0  # normalize
    img_array = np.expand_dims(img_array, axis=0)  # shape (1, 224, 224, 3)
    return img_array

# --- 3. Predict Function ---
def predict_image(image_path):
    """Predicts the class of a given image path."""
    img_array = load_and_preprocess_image(image_path)
    predictions = model.predict(img_array)
    predicted_class_idx = np.argmax(predictions, axis=1)[0]
    confidence = np.max(predictions)

    predicted_class = CLASS_NAMES[predicted_class_idx]
    print(f"\nImage: {image_path}")
    print(f"Predicted Class: {predicted_class}")
    print(f"Confidence: {confidence:.2f}")

# --- 4. Run from Command Line ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python predict.py <image_path1> [<image_path2> ...]")
        sys.exit(1)

    image_paths = sys.argv[1:]
    for image_path in image_paths:
        if not os.path.exists(image_path):
            print(f"Error: File not found -> {image_path}")
        else:
            predict_image(image_path)
