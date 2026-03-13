"""Web UI using Streamlit - Optimized."""
import streamlit as st
import yaml
from pathlib import Path
import shutil
import concurrent.futures
from typing import Optional
import time

from photofilter.core import Photo, ImageAnalyzer, SemanticMatcher, FilterEngine, get_matcher
from photofilter.config import ConfigManager


st.set_page_config(
    page_title="Photo Filter", 
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded"
)


class WebUI:
    def __init__(self):
        self.analyzer = ImageAnalyzer()
        self.semantic_matcher = None
        self.config_manager = ConfigManager()
    
    def run(self):
        st.title("📷 Photo Filter 智能照片筛选")
        
        # Sidebar
        with st.sidebar:
            st.header("配置")
            
            # Config upload
            config_file = st.file_uploader("配置文件 (YAML)", type=['yaml', 'yml'])
            
            if config_file:
                config_data = yaml.safe_load(config_file)
            else:
                config_data = {
                    "social_media": {
                        "enabled": True,
                        "basic_filters": {
                            "resolution": {"min_width": 800, "min_height": 600},
                            "formats": ["jpg", "jpeg", "png"]
                        },
                        "semantic_matching": {"enabled": False},
                        "output": {"top_n": 20}
                    }
                }
            
            workers = st.slider("线程数", 1, 8, 4)
            use_clip = st.checkbox("启用CLIP", value=False)
        
        # Main inputs
        input_dir = st.text_input("输入目录", "./photos")
        output_dir = st.text_input("输出目录", "./output")
        
        # Purposes
        purposes = [k for k, v in config_data.items() if v.get('enabled', True)]
        selected = st.multiselect("筛选目的", purposes, default=purposes)
        
        # Run
        if st.button("开始筛选"):
            if not Path(input_dir).exists():
                st.error("目录不存在")
                return
            
            if use_clip:
                with st.spinner("加载CLIP..."):
                    self.semantic_matcher = SemanticMatcher()
            
            photos_files = self._scan_photos(Path(input_dir))
            st.info(f"找到 {len(photos_files)} 张照片")
            
            if not photos_files:
                return
            
            with st.spinner("分析中..."):
                photos = self._process_photos(photos_files, workers)
            
            for purpose in selected:
                rule = config_data[purpose]
                engine = FilterEngine({purpose: rule})
                filtered = []
                
                for photo in photos:
                    passes, score = engine.apply(photo, purpose)
                    if passes:
                        photo.match_scores[purpose] = score
                        filtered.append((photo, score))
                
                filtered.sort(key=lambda x: x[1], reverse=True)
                top_n = rule.get('output', {}).get('top_n', len(filtered))
                filtered = filtered[:top_n]
                
                st.success(f"{purpose}: {len(filtered)}/{len(photos)}")
                
                if output_dir:
                    save_path = Path(output_dir) / purpose
                    save_path.mkdir(parents=True, exist_ok=True)
                    for photo, _ in filtered:
                        shutil.copy2(photo.path, save_path / photo.filename)
                
                if filtered:
                    st.subheader(f"{purpose} 预览")
                    cols = st.columns(4)
                    for i, (photo, score) in enumerate(filtered[:8]):
                        with cols[i % 4]:
                            st.image(str(photo.path), caption=f"{photo.filename}\n{score:.1f}")
            
            st.balloons()
    
    def _scan_photos(self, directory: Path) -> list:
        exts = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'}
        photos = []
        for ext in exts:
            photos.extend(directory.glob(f"*{ext}"))
            photos.extend(directory.glob(f"*{ext.upper()}"))
        return sorted(photos)
    
    def _process_photos(self, photo_files: list, workers: int) -> list:
        photos = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self._analyze_photo, f): f for f in photo_files}
            for future in concurrent.futures.as_completed(futures):
                photo = future.result()
                if photo:
                    photos.append(photo)
        return photos
    
    def _analyze_photo(self, path: Path) -> Optional[Photo]:
        photo = Photo(path=path, filename=path.name)
        photo = self.analyzer.analyze(photo)
        photo = self.analyzer.detect_faces(photo)
        
        if self.semantic_matcher:
            keywords = []
            for rule in self.config_manager.get_all_rules().values():
                if rule.get('semantic_matching', {}).get('enabled'):
                    keywords.extend(rule.get('semantic_matching', {}).get('keywords', []))
            if keywords:
                keywords = list(set(keywords))
                photo.clip_scores = self.semantic_matcher.match_photo(photo, keywords)
        
        return photo


if __name__ == "__main__":
    WebUI().run()
