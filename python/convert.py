import tensorflow as tf

# Load your trained model
model = tf.keras.models.load_model('models/socket_classifier_v1.h5')

# Convert it
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# Save the new file
with open('models/socket_classifier_v1.tflite', 'wb') as f:
    f.write(tflite_model)

print("Done! Created socket_classifier_v1.tflite")