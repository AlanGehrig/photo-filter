"""CLI interface."""
import argparse
import sys
from pathlib import Path
from typing import Optional
import concurrent.futures
import shutil

from photofilter.core import Photo, ImageAnalyzer, SemanticMatcher, FilterEngine
from photofilter.config import ConfigManager


class CLI:
    def __init__(self):
        self.parser = self._build_parser()
        self.analyzer = ImageAnalyzer()
        self.semantic_matcher = None
        self.config_manager = ConfigManager()
    
    def _build_parser(self):
        parser = argparse.ArgumentParser(prog="photo-filter", description="智能照片筛选工具")
        parser.add_argument("--config", "-c", required=True, help="YAML配置文件")
        parser.add_argument("--input", "-i", required=True, help="输入目录")
        parser.add_argument("--output", "-o", required=True, help="输出目录")
        parser.add_argument("--purpose", "-p", help="筛选目的")
        parser.add_argument("--preview", "-v", action="store_true", help="预览模式")
        parser.add_argument("--workers", "-w", type=int, default=4, help="线程数")
        parser.add_argument("--no-clip", action="store_true", help="禁用CLIP")
        return parser
    
    def run(self, args: Optional[list] = None):
        parsed = self.parser.parse_args(args)
        
        # Load config
        try:
            rules = self.config_manager.load(parsed.config)
        except FileNotFoundError as e:
            print(f"错误: {e}")
            sys.exit(1)
        
        # Purposes
        if parsed.purpose:
            purposes = [parsed.purpose]
        else:
            purposes = [n for n, r in rules.items() if r.get('enabled', True)]
        
        print(f"处理: {', '.join(purposes)}")
        
        # Scan photos
        input_path = Path(parsed.input)
        photo_files = self._scan_photos(input_path)
        print(f"找到 {len(photo_files)} 张照片")
        
        if not photo_files:
            sys.exit(0)
        
        # Semantic matcher
        if not parsed.no_clip:
            print("加载CLIP...")
            self.semantic_matcher = SemanticMatcher()
        
        # Process
        print(f"处理中 ({parsed.workers} 线程)...")
        photos = self._process_photos(photo_files, parsed.workers)
        
        # Filter each purpose
        for purpose in purposes:
            rule = rules[purpose]
            engine = FilterEngine({purpose: rule})
            filtered = []
            
            for photo in photos:
                passes, score = engine.apply(photo, purpose)
                if passes:
                    photo.match_scores[purpose] = score
                    filtered.append((photo, score))
            
            # Sort & limit
            sort_by = rule.get('output', {}).get('sort_by', 'match_score')
            top_n = rule.get('output', {}).get('top_n', len(filtered))
            
            if sort_by == 'quality':
                filtered.sort(key=lambda x: x[0].quality_score, reverse=True)
            else:
                filtered.sort(key=lambda x: x[1], reverse=True)
            
            filtered = filtered[:top_n]
            print(f"{purpose}: {len(filtered)}/{len(photos)} 通过")
            
            if not parsed.preview:
                save_path = Path(rule.get('output', {}).get('save_path', parsed.output))
                save_path.mkdir(parents=True, exist_ok=True)
                for photo, score in filtered:
                    shutil.copy2(photo.path, save_path / photo.filename)
        
        print("完成!")
    
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


def main():
    CLI().run()


if __name__ == "__main__":
    main()
