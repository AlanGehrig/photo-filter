"""Semantic matching using CLIP - Optimized."""
from typing import Optional, List
import numpy as np
import torch
from functools import lru_cache
from PIL import Image


# Singleton instance
_matcher_instance = None


def get_matcher(model_name: str = "openai/clip-vit-base-patch32") -> "SemanticMatcher":
    """Get singleton SemanticMatcher instance."""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = SemanticMatcher(model_name)
    return _matcher_instance


class SemanticMatcher:
    """Match photos to purposes using CLIP - Optimized with GPU & batching."""
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        self.model_name = model_name
        self.model = None
        self.processor = None
        self.device = None
        self._loaded = False
    
    def load(self):
        """Load CLIP model with GPU support."""
        if self._loaded:
            return
        
        # Auto-detect GPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            from transformers import CLIPProcessor, CLIPModel
            self.model = CLIPModel.from_pretrained(self.model_name).to(self.device)
            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            self.model.eval()
            self._loaded = True
            print(f"CLIP loaded on {self.device}: {self.model_name}")
        except Exception as e:
            print(f"Failed to load CLIP: {e}")
            self.device = "cpu"
    
    def is_loaded(self) -> bool:
        return self._loaded and self.model is not None
    
    def match_keywords(self, image_path: str, keywords: List[str]) -> dict:
        """Match single image against keywords."""
        if not self.is_loaded():
            self.load()
        if not self.is_loaded():
            return {kw: 0.0 for kw in keywords}
        
        try:
            image = Image.open(image_path).convert('RGB')
            inputs = self.processor(
                text=keywords, 
                images=image, 
                return_tensors="pt", 
                padding=True
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = outputs.logits_per_image.softmax(dim=1)[0]
            
            return {kw: float(probs[i]) for i, kw in enumerate(keywords)}
        except Exception as e:
            print(f"Semantic error: {e}")
            return {kw: 0.0 for kw in keywords}
    
    def match_batch(self, image_paths: List[str], keywords: List[str], batch_size: int = 8) -> List[dict]:
        """Match multiple images in batches - MUCH faster."""
        if not self.is_loaded():
            self.load()
        if not self.is_loaded():
            return [{kw: 0.0 for kw in keywords}] * len(image_paths)
        
        results = []
        
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            batch_images = []
            
            for path in batch_paths:
                try:
                    img = Image.open(path).convert('RGB')
                    batch_images.append(img)
                except Exception as e:
                    print(f"Failed to open {path}: {e}")
                    batch_images.append(Image.new('RGB', (224, 224)))
            
            try:
                inputs = self.processor(
                    text=keywords,
                    images=batch_images,
                    return_tensors="pt",
                    padding=True
                ).to(self.device)
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    probs = outputs.logits_per_image  # [batch_size, num_keywords]
                    probs = probs.softmax(dim=1)
                
                for j in range(len(batch_paths)):
                    results.append({kw: float(probs[j, i]) for i, kw in enumerate(keywords)})
                    
            except Exception as e:
                print(f"Batch error: {e}")
                results.extend([{kw: 0.0 for kw in keywords}] * len(batch_paths))
        
        return results
    
    def match_photo(self, photo, keywords: List[str]) -> dict:
        """Match photo object against keywords."""
        return self.match_keywords(str(photo.path), keywords)
    
    def match_photos_batch(self, photos: list, keywords: List[str], batch_size: int = 8) -> List[dict]:
        """Match multiple photo objects in batches."""
        paths = [str(p.path) for p in photos]
        return self.match_batch(paths, keywords, batch_size)
    
    def clear_cache(self):
        """Clear GPU cache."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
