import cv2
import numpy as np
import os
import re

def natural_sort_key(s: str):
    """
    Sort strings with numbers in natural order (e.g. 1.jpg, 2.jpg, 10.jpg)
    Matches the way Windows Explorer and most file managers sort.
    """
    if not s:
        return []
    # Use basename for sorting if it's a full path
    name = os.path.basename(s)
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', name)]

def cv2_imread(file_path: str, flags: int = cv2.IMREAD_COLOR) -> np.ndarray:
    """
    Read an image from a file path, supporting non-ASCII characters (like Chinese).
    """
    try:
        # Read file as raw bytes
        img_array = np.fromfile(file_path, dtype=np.uint8)
        # Decode the bytes into an image
        img = cv2.imdecode(img_array, flags)
        return img
    except Exception as e:
        print(f"Error reading image {file_path}: {e}")
        return None

def cv2_imwrite(file_path: str, img: np.ndarray, params: list = None) -> bool:
    """
    Write an image to a file path, supporting non-ASCII characters (like Chinese).
    """
    try:
        # Get file extension
        ext = os.path.splitext(file_path)[1]
        # Encode the image into memory
        result, nparray = cv2.imencode(ext, img, params)
        if result:
            # Write bytes to file
            with open(file_path, 'wb') as f:
                nparray.tofile(f)
            return True
        return False
    except Exception as e:
        print(f"Error writing image {file_path}: {e}")
        return False
