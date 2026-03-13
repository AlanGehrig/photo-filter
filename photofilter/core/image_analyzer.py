"""Image quality analysis."""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional
from .photo import Photo


class ImageAnalyzer:
    """Analyzes image quality metrics."""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'}
    
    def analyze(self, photo: Photo) -> Photo:
        if not self._is_supported(photo.path):
            return photo
        
        try:
            img = cv2.imread(str(photo.path))
            if img is None:
                return photo
            
            photo.width = img.shape[1]
            photo.height = img.shape[0]
            photo.format = photo.path.suffix.lower()
            photo.size_bytes = photo.path.stat().st_size
            
            photo.blur_score = self._calculate_blur(img)
            photo.exposure_score, photo.is_overexposed, photo.is_underexposed = self._calculate_exposure(img)
            photo.noise_level = self._calculate_noise(img)
            
            return photo
        except Exception as e:
            print(f"Error analyzing {photo.path}: {e}")
            return photo
    
    def _is_supported(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_FORMATS
    
    def _calculate_blur(self, img) -> float:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return laplacian.var()
    
    def _calculate_exposure(self, img) -> tuple:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean = gray.mean() / 255.0
        is_over = mean > 0.85
        is_under = mean < 0.15
        optimal = 0.5
        score = max(0.0, min(1.0, 1.0 - abs(mean - optimal) * 2))
        return score, is_over, is_under
    
    def _calculate_noise(self, img) -> float:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        median = np.median(gray)
        sigma = np.median(np.abs(gray - median)) / 0.6745
        return sigma / 255.0
    
    def detect_faces(self, photo: Photo) -> Photo:
        try:
            import cv2
            img = cv2.imread(str(photo.path))
            if img is None:
                return photo
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
            
            photo.has_face = len(faces) > 0
            photo.face_count = len(faces)
            photo.face_boxes = [tuple(f) for f in faces]
        except Exception as e:
            print(f"Face detection error: {e}")
        
        return photo
