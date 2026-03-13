"""Filtering engine."""
from typing import Optional
from .photo import Photo


class FilterEngine:
    """Applies filter rules to photos."""
    
    def __init__(self, rules: dict):
        self.rules = rules
    
    def apply(self, photo: Photo, purpose: str) -> tuple[bool, float]:
        if purpose not in self.rules:
            return False, 0.0
        
        rule = self.rules[purpose]
        if not rule.get('enabled', True):
            return False, 0.0
        
        score = 0.0
        max_score = 0.0
        
        # Basic filters
        basic = rule.get('basic_filters', {})
        passes_basic, basic_score = self._apply_basic_filters(photo, basic)
        score += basic_score
        max_score += 100
        
        if not passes_basic:
            return False, 0.0
        
        # Semantic matching
        semantic = rule.get('semantic_matching', {})
        if semantic.get('enabled', False):
            semantic_score = self._apply_semantic(photo, semantic)
            score += semantic_score * 100
            max_score += 100
        else:
            score += 100
            max_score += 100
        
        final_score = (score / max_score) * 100 if max_score > 0 else 0.0
        return True, final_score
    
    def _apply_basic_filters(self, photo: Photo, filters: dict) -> tuple[bool, float]:
        score = 0.0
        max_items = 0
        
        # Resolution
        if 'resolution' in filters:
            res = filters['resolution']
            max_items += 2
            if photo.width and photo.height:
                if photo.width >= res.get('min_width', 0) and photo.height >= res.get('min_height', 0):
                    score += 2
        
        # Blur
        if 'blur_score' in filters:
            max_items += 1
            if photo.blur_score is not None and photo.blur_score >= filters['blur_score'].get('max', 0):
                score += 1
        
        # Exposure
        if 'exposure' in filters:
            exp = filters['exposure']
            max_items += 1
            if photo.exposure_score is not None:
                if exp.get('min', 0) <= photo.exposure_score <= exp.get('max', 1):
                    score += 1
        
        # Format
        if 'formats' in filters:
            max_items += 1
            if photo.format and photo.format.lstrip('.') in filters['formats']:
                score += 1
        
        # Face detection
        if 'face_detection' in filters:
            fd = filters['face_detection']
            max_items += 1
            if fd.get('required', False) and photo.has_face:
                score += 1
        
        passes = score > 0
        return passes, (score / max_items * 100) if max_items > 0 else 0.0
    
    def _apply_semantic(self, photo: Photo, config: dict) -> float:
        keywords = config.get('keywords', [])
        threshold = config.get('match_threshold', 0.0)
        
        if not keywords or not photo.clip_scores:
            return 0.0
        
        scores = [photo.clip_scores.get(kw, 0.0) for kw in keywords if kw in photo.clip_scores]
        if not scores:
            return 0.0
        
        avg = sum(scores) / len(scores)
        return avg if avg >= threshold else 0.0
