import cv2
import numpy as np
from typing import List, Tuple, Optional

def create_blob_detector(min_area: int = 50, max_area: int = 1500, 
                        use_circularity: bool = True, min_circularity: float = 0.4):
    """Create a configured cv2.SimpleBlobDetector"""
    params = cv2.SimpleBlobDetector_Params()
    
    # Filter by Area
    params.filterByArea = True
    params.minArea = float(min_area)
    params.maxArea = float(max_area)
    
    # Filter by Circularity
    params.filterByCircularity = use_circularity
    if use_circularity:
        params.minCircularity = min_circularity
        
    # Disable other filters for performance and consistency
    for flag in ("filterByConvexity", "filterByInertia", "filterByColor"):
        setattr(params, flag, False)
        
    params.minThreshold = 10
    params.maxThreshold = 220
    params.thresholdStep = 10
    
    return cv2.SimpleBlobDetector_create(params)

def detect_cells_in_roi(img: np.ndarray, mask: np.ndarray, min_area=20, max_area=1500, 
                        use_circularity: bool = True, min_circularity: float = 0.4) -> List[Tuple]:
    """
    Restore to original SimpleBlobDetector as requested.
    """
    if img is None:
        return []
        
    # 1. Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Create detector
    detector = create_blob_detector(min_area, max_area, use_circularity, min_circularity)
    
    # 3. Detect
    keypoints = detector.detect(gray)
    
    cells = []
    h, w = gray.shape[:2]
    
    for kp in keypoints:
        cx, cy = kp.pt
        
        # 4. Filter by ROI mask
        if mask is not None:
            ix, iy = int(cx), int(cy)
            if 0 <= ix < w and 0 <= iy < h:
                if mask[iy, ix] == 0:
                    continue
            else:
                continue
                
        # Store as (x, y, size)
        cells.append((int(cx), int(cy), float(kp.size)))
        
    return cells

def auto_count_cells_full_image(image: np.ndarray, min_area=50, max_area=1500, circularity_threshold=0.4):
    """Automatically detect cells in the entire image using contour analysis"""
    if image is None:
        return [], None
        
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2
    )
    
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cells = []
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area or area > max_area:
            continue
        
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            continue
        
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        if circularity < circularity_threshold:
            continue
        
        M = cv2.moments(contour)
        if M["m00"] == 0:
            continue
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        cells.append((cx, cy))
    
    return cells, thresh
