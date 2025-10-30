import tensorflow as tf
import os

# --- Configuration ---
IMG_SIZE = (224, 224)
BATCH_SIZE = 32 # Number of images to process at a time
EPOCHS = 10     # Number of times to go through the entire dataset
NUM_CLASSES = 3 # The number of socket sizes you are classifying

TRAIN_DIR = '../dataset/train'
VALIDATION_DIR = '../dataset/validation'
MODEL_SAVE_PATH = '../models/socket_classifier_v1.h5'

# --- 1. Load the Pre-trained Base Model ---
# We use MobileNetV2, a powerful and efficient CNN
base_model = tf.keras.applications.MobileNetV2(input_shape=IMG_SIZE + (3,),
                                               include_top=False,
                                               weights='imagenet')

# --- 2. Freeze the Base Model ---
# This prevents the learned weights of MobileNetV2 from changing
base_model.trainable = False

# --- 3. Add Your Custom Classification Head ---
# We stack our own layers on top of the base model
model = tf.keras.Sequential([
  base_model,
  tf.keras.layers.GlobalAveragePooling2D(),
  tf.keras.layers.Dense(NUM_CLASSES, activation='softmax')
])

# --- 4. Compile the Model ---
# This configures the model for training
model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])

# --- 5. Prepare the Data ---
# Create data generators that will read images from your folders
# and automatically label them based on the folder names.
train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1./255)
validation_datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1./255)

train_generator = train_datagen.flow_from_directory(
    TRAIN_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical'
)

validation_generator = validation_datagen.flow_from_directory(
    VALIDATION_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical'
)

# --- 6. Train the Model ---
print("Starting model training...")
history = model.fit(
    train_generator,
    epochs=EPOCHS,
    validation_data=validation_generator
)
print("Training finished!")

# --- 7. Save the Trained Model ---
# This is the most important step! It saves the entire model to a single file.
os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True) # Ensure the directory exists
model.save(MODEL_SAVE_PATH)

print(f"Model saved successfully to {MODEL_SAVE_PATH}")