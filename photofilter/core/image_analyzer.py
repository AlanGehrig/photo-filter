"""Image quality analysis - Optimized with caching."""
import cv2
import numpy as np
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict
from functools import lru_cache
from .photo import Photo


class ImageAnalyzer:
    """Analyzes image quality metrics - Optimized with caching & batch processing."""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'}
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".photo-filter" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, dict] = {}
    
    def _get_cache_key(self, photo: Photo) -> str:
        """Generate cache key from file path and modification time."""
        stat = photo.path.stat()
        key_str = f"{photo.path}:{stat.st_mtime}:{stat.st_size}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _load_cache(self, photo: Photo) -> Optional[dict]:
        """Load analysis result from cache."""
        cache_key = self._get_cache_key(photo)
        
        # Check memory cache first
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    self._memory_cache[cache_key] = data
                    return data
            except Exception:
                pass
        return None
    
    def _save_cache(self, photo: Photo, data: dict):
        """Save analysis result to cache."""
        cache_key = self._get_cache_key(photo)
        self._memory_cache[cache_key] = data
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Cache write error: {e}")
    
    def analyze(self, photo: Photo) -> Photo:
        if not self._is_supported(photo.path):
            return photo
        
        # Try cache first
        cached = self._load_cache(photo)
        if cached:
            photo.width = cached.get('width', 0)
            photo.height = cached.get('height', 0)
            photo.format = cached.get('format', '')
            photo.size_bytes = cached.get('size_bytes', 0)
            photo.blur_score = cached.get('blur_score', 0)
            photo.exposure_score = cached.get('exposure_score', 0)
            photo.is_overexposed = cached.get('is_overexposed', False)
            photo.is_underexposed = cached.get('is_underexposed', False)
            photo.noise_level = cached.get('noise_level', 0)
            return photo
        
        # Perform analysis
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
            
            # Save to cache
            self._save_cache(photo, {
                'width': photo.width,
                'height': photo.height,
                'format': photo.format,
                'size_bytes': photo.size_bytes,
                'blur_score': photo.blur_score,
                'exposure_score': photo.exposure_score,
                'is_overexposed': photo.is_overexposed,
                'is_underexposed': photo.is_underexposed,
                'noise_level': photo.noise_level,
            })
            
            return photo
        except Exception as e:
            print(f"Error analyzing {photo.path}: {e}")
            return photo
    
    def analyze_batch(self, photos: list, show_progress: bool = False) -> list:
        """Analyze multiple photos efficiently."""
        results = []
        total = len(photos)
        
        for i, photo in enumerate(photos):
            results.append(self.analyze(photo))
            if show_progress and (i + 1) % 10 == 0:
                print(f"Processed {i+1}/{total}")
        
        return results
    
    def clear_cache(self):
        """Clear all caches."""
        self._memory_cache.clear()
        for f in self.cache_dir.glob("*.json"):
            try:
                f.unlink()
            except Exception:
                pass
    
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
