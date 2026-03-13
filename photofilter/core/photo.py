"""Photo data model."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from datetime import datetime


@dataclass
class Photo:
    """Represents a photo with metadata and analysis results."""
    
    path: Path
    filename: str
    
    # Basic metadata
    format: Optional[str] = None
    size_bytes: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    created_time: Optional[datetime] = None
    
    # Image quality metrics
    blur_score: Optional[float] = None
    exposure_score: Optional[float] = None
    noise_level: Optional[float] = None
    is_overexposed: Optional[bool] = None
    is_underexposed: Optional[bool] = None
    
    # Content analysis
    has_face: Optional[bool] = None
    face_count: int = 0
    face_boxes: list = None
    
    # Semantic matching
    clip_scores: dict = None
    
    # Final scores
    quality_score: float = 0.0
    match_scores: dict = None
    
    def __post_init__(self):
        if self.face_boxes is None:
            self.face_boxes = []
        if self.clip_scores is None:
            self.clip_scores = {}
        if self.match_scores is None:
            self.match_scores = {}
    
    @property
    def resolution(self) -> Optional[tuple]:
        if self.width and self.height:
            return (self.width, self.height)
        return None
    
    @property
    def megapixels(self) -> Optional[float]:
        if self.width and self.height:
            return (self.width * self.height) / 1_000_000
        return None
