"""Semantic matching using CLIP."""
from typing import Optional
import numpy as np


class SemanticMatcher:
    """Match photos to purposes using CLIP."""
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        self.model_name = model_name
        self.model = None
        self.processor = None
        self._loaded = False
    
    def load(self):
        if self._loaded:
            return
        try:
            from transformers import CLIPProcessor, CLIPModel
            self.model = CLIPModel.from_pretrained(self.model_name)
            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            self._loaded = True
            print(f"CLIP loaded: {self.model_name}")
        except Exception as e:
            print(f"Failed to load CLIP: {e}")
    
    def is_loaded(self) -> bool:
        return self._loaded and self.model is not None
    
    def match_keywords(self, image_path: str, keywords: list) -> dict:
        if not self.is_loaded():
            self.load()
        if not self.is_loaded():
            return {kw: 0.0 for kw in keywords}
        
        try:
            from PIL import Image
            import torch
            image = Image.open(image_path).convert('RGB')
            inputs = self.processor(text=keywords, images=image, return_tensors="pt", padding=True)
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = outputs.logits_per_image.softmax(dim=1)[0]
            return {kw: float(probs[i]) for i, kw in enumerate(keywords)}
        except Exception as e:
            print(f"Semantic error: {e}")
            return {kw: 0.0 for kw in keywords}
    
    def match_photo(self, photo, keywords: list) -> dict:
        return self.match_keywords(str(photo.path), keywords)
