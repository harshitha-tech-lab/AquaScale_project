# AquaScale_project
Fish Growth Analysis and Fish Mass Prediction Using Deep Learning project


## Overview
Fish Growth Analysis and Fish Mass Prediction Using Deep Learning is an AI-powered web application developed to automate fish monitoring in aquaculture. The system identifies fish species, estimates fish length, predicts body mass, and determines growth stages from a single image using Deep Learning and Computer Vision techniques.

This project reduces manual effort, minimizes fish handling stress, and helps farmers make data-driven decisions for feeding and harvesting.

## Features

- Fish Species Classification
  - Identifies fish species using a CNN model.
  - Supported species:
    - Tilapia
    - Snakehead

- Fish Detection
  - Uses YOLOv8-World for fish and reference object detection.

- Instance Segmentation
  - Uses FastSAM to extract accurate fish contours and measurements.

- Length Estimation
  - Calculates real-world fish length using a reference measurement object.

- Weight Prediction
  - Predicts fish mass using biological length-weight relationships.

- Growth Stage Identification
  - Classifies fish into:
    - Juvenile
    - Growing
    - Mature

- User Authentication
  - Secure registration and login system.

- Analysis History
  - Stores previous analysis results for future reference.

## Technologies Used

### Backend
- Python
- Flask
- Flask-Login
- SQLite3

### Deep Learning & Computer Vision
- TensorFlow
- Keras
- YOLOv8-World
- FastSAM
- OpenCV

### Frontend
- HTML5
- CSS3
- JavaScript

## System Workflow

1. Upload fish image.
2. YOLOv8 detects fish and reference object.
3. Fish region is cropped automatically.
4. CNN classifies fish species.
5. FastSAM performs segmentation.
6. Fish length is estimated using pixel-to-centimeter scaling.
7. Fish weight is predicted.
8. Growth stage is determined.
9. Results are displayed and stored.

