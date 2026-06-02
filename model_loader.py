import cv2
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
import numpy as np
import os

MODEL_PATH_H5 = 'final_weight_classification.h5'

def load_classification_model():
    """Loads the pre-trained classification model."""
    if not os.path.exists(MODEL_PATH_H5):
        print(f"Error: Model not found at {MODEL_PATH_H5}")
        return None
    
    print(f"Loading model from {MODEL_PATH_H5}...")
    try:
        model = load_model(MODEL_PATH_H5)
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

def classify_fish(model, image_input):
    """Classifies the fish image (path or crop) as Tilapia or Snakehead."""
    if model is None:
        return "Model not loaded"

    try:
        # Load and preprocess image
        if isinstance(image_input, str):
            # Path
            img = image.load_img(image_input, target_size=(128, 128))
            img_array = image.img_to_array(img)
        elif isinstance(image_input, np.ndarray):
            # Cropped CV2 image (BGR). Convert to RGB and Resize.
            img_rgb = cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB)
            img_resized = cv2.resize(img_rgb, (128, 128))
            img_array = image.img_to_array(img_resized)
        else:
            return "Invalid Input"

        img_array = np.expand_dims(img_array, axis=0)
        img_array /= 255.0

        prediction = model.predict(img_array)
        
        # Class 0 (Snakehead), Class 1 (Tilapia)
        predicted_class_index = int(prediction[0][0] > 0.5) 
        
        classes = ['Snakehead', 'Tilapia']
        confidence = prediction[0][0]
        
        print(f"Prediction raw: {confidence}, Class: {classes[predicted_class_index]}")
        
        return classes[predicted_class_index]

    except Exception as e:
        print(f"Classification error: {e}")
        return "Error"
