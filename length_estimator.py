import cv2
import numpy as np
import os
from ultralytics import FastSAM, YOLOWorld

# Constants
YOLO_MODEL_PATH = 'yolov8s-world.pt'
FASTSAM_MODEL_PATH = 'FastSAM-s.pt'

model_det = None
model_seg = None

def get_models():
    global model_det, model_seg
    if model_det is None:
        if os.path.exists(YOLO_MODEL_PATH):
            model_det = YOLOWorld(YOLO_MODEL_PATH)
            model_det.set_classes(["fish", "dried fish", "orange rectangle", "orange paper", "orange strip"])
        else:
            print("YOLO Model not found.")
    
    if model_seg is None:
        if os.path.exists(FASTSAM_MODEL_PATH):
            model_seg = FastSAM(FASTSAM_MODEL_PATH)
        else:
            print("FastSAM Model not found.")
    
    return model_det, model_seg

def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    iou = interArea / float(boxAArea + boxBArea - interArea + 1e-6)
    return iou

def find_reference_by_color(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_orange = np.array([0, 50, 50])
    upper_orange = np.array([40, 255, 255])
    mask = cv2.inRange(hsv, lower_orange, upper_orange)
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours: return None
    valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 500]
    if not valid_contours: return None
    return max(valid_contours, key=cv2.contourArea)

def detect_and_crop(image_path):
    """
    Step 1: Detects fish using YOLO, crops it for classification.
    Uses cached YOLO model.
    """
    model_det, _ = get_models()
    if model_det is None:
        return None

    original_img = cv2.imread(image_path)
    if original_img is None:
        return None

    img_h, img_w = original_img.shape[:2]

    # Predict
    results_det = model_det.predict(image_path, conf=0.01, verbose=False)
    
    det_boxes = []
    if results_det[0].boxes:
        det_boxes = results_det[0].boxes.data.cpu().numpy()

    fish_box = None
    target_classes_fish = ["fish", "dried fish"]
    custom_classes = ["fish", "dried fish", "orange rectangle", "orange paper", "orange strip"]

    for box in det_boxes:
        x1, y1, x2, y2, conf, cls_id = box
        label_idx = int(cls_id)
        if label_idx < len(custom_classes):
            label = custom_classes[label_idx]
            if label in target_classes_fish:
                current_area = (x2-x1)*(y2-y1)
                if fish_box is None or current_area > (fish_box[2]-fish_box[0])*(fish_box[3]-fish_box[1]):
                    fish_box = [x1, y1, x2, y2]

    if fish_box is None:
        return None

    # Crop
    x1, y1, x2, y2 = map(int, fish_box)
    pad = 10
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(img_w, x2 + pad)
    y2 = min(img_h, y2 + pad)
    
    crop = original_img[y1:y2, x1:x2]
    return crop


def calculate_segmentation_metrics(image_path):
    """
    Step 2: Detects and Segments everything to calculate pixels.
    Uses cached models.
    """
    model_det, model_seg = get_models()
    
    if model_det is None or model_seg is None:
        return 0, 0, image_path

    original_img = cv2.imread(image_path)
    if original_img is None:
        return 0, 0, image_path
    
    img_h, img_w = original_img.shape[:2]

    # Predict
    results_det = model_det.predict(image_path, conf=0.01, verbose=False)
    results_seg = model_seg(image_path, device='cpu', retina_masks=True, conf=0.2, verbose=False)

    det_boxes = []
    if results_det[0].boxes:
        det_boxes = results_det[0].boxes.data.cpu().numpy()
    
    seg_masks = []
    if results_seg and results_seg[0].masks:
        seg_masks = results_seg[0].masks.data.cpu().numpy()

    # Process Detections
    fish_contour = None
    ref_contour = None

    def get_mask_box(mask):
        y_indices, x_indices = np.where(mask > 0)
        if len(x_indices) == 0: return [0, 0, 0, 0]
        return [np.min(x_indices), np.min(y_indices), np.max(x_indices), np.max(y_indices)]

    def box_to_contour(x1, y1, x2, y2):
        return np.array([[[int(x1), int(y1)]], [[int(x2), int(y1)]], 
                         [[int(x2), int(y2)]], [[int(x1), int(y2)]]], dtype=np.int32)

    custom_classes = ["fish", "dried fish", "orange rectangle", "orange paper", "orange strip"]
    target_classes_fish = ["fish", "dried fish"]
    target_classes_ref = ["orange rectangle", "orange paper", "orange strip"]

    for box in det_boxes:
        x1, y1, x2, y2, conf, cls_id = box
        label_idx = int(cls_id)
        if label_idx < len(custom_classes):
            label = custom_classes[label_idx]
        else:
            continue

        category = None
        if label in target_classes_fish: category = "fish"
        elif label in target_classes_ref: category = "reference"
        
        if category is None: continue

        det_box = [x1, y1, x2, y2]
        
        # Match Mask
        best_iou = 0
        best_mask = None

        for mask_tensor in seg_masks:
            mask_uint8 = (mask_tensor * 255).astype(np.uint8)
            if mask_uint8.shape[:2] != (img_h, img_w):
                mask_uint8 = cv2.resize(mask_uint8, (img_w, img_h), interpolation=cv2.INTER_NEAREST)
            
            mask_box = get_mask_box(mask_uint8)
            iou = calculate_iou(det_box, mask_box)
            if iou > best_iou:
                best_iou = iou
                best_mask = mask_uint8
        
        current_cnt = None
        if best_iou > 0.3:
            contours, _ = cv2.findContours(best_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                cnt = max(contours, key=cv2.contourArea)
                if cv2.contourArea(cnt) > 500:
                    current_cnt = cnt
        
        if current_cnt is None:
            current_cnt = box_to_contour(x1, y1, x2, y2)

        if category == "fish":
            if fish_contour is None or cv2.contourArea(current_cnt) > cv2.contourArea(fish_contour):
                fish_contour = current_cnt
        elif category == "reference":
            if ref_contour is None or cv2.contourArea(current_cnt) > cv2.contourArea(ref_contour):
                ref_contour = current_cnt

    if ref_contour is None:
        ref_contour = find_reference_by_color(original_img)

    # Process metrics and draw
    result_path = image_path.replace('.', '_processed.')
    fish_pixel_len = 0.0
    ref_pixel_len = 0.0

    if ref_contour is not None:
        rect_ref = cv2.minAreaRect(ref_contour)
        ref_pixel_len = max(rect_ref[1])
        cv2.drawContours(original_img, [ref_contour], 0, (0, 165, 255), 3)
        box_ref = np.int32(cv2.boxPoints(rect_ref))
        cv2.putText(original_img, "Ref", (box_ref[0][0], box_ref[0][1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)

    if fish_contour is not None:
        rect_fish = cv2.minAreaRect(fish_contour)
        fish_pixel_len = max(rect_fish[1])
        cv2.drawContours(original_img, [fish_contour], 0, (255, 0, 0), 3)
        box_fish = np.int32(cv2.boxPoints(rect_fish))
        cv2.putText(original_img, "Fish", (box_fish[0][0], box_fish[0][1]-20), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 3)
    
    cv2.imwrite(result_path, original_img)
    return fish_pixel_len, ref_pixel_len, os.path.basename(result_path)
