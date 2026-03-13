"""Windows GUI using PyQt5."""
import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QProgressBar,
    QTextEdit, QComboBox, QCheckBox, QGroupBox, QScrollArea,
    QListWidget, QMessageBox, QSlider
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
import yaml
import shutil
import concurrent.futures

from photofilter.core import Photo, ImageAnalyzer, SemanticMatcher, FilterEngine
from photofilter.config import ConfigManager


class FilterWorker(QThread):
    """Background worker for filtering."""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, input_dir, output_dir, config_data, selected_purposes, use_clip, workers):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.config_data = config_data
        self.selected_purposes = selected_purposes
        self.use_clip = use_clip
        self.workers = workers
    
    def run(self):
        try:
            analyzer = ImageAnalyzer()
            semantic_matcher = None
            
            if self.use_clip:
                self.status.emit("加载CLIP模型...")
                semantic_matcher = SemanticMatcher()
            
            # Scan photos
            self.status.emit("扫描照片...")
            photo_files = self._scan_photos(Path(self.input_dir))
            self.status.emit(f"找到 {len(photo_files)} 张照片")
            
            if not photo_files:
                self.error.emit("未找到照片")
                return
            
            # Process photos
            photos = self._process_photos(photo_files, analyzer, semantic_matcher)
            
            # Filter
            results = {}
            for purpose in self.selected_purposes:
                self.status.emit(f"筛选: {purpose}")
                rule = self.config_data[purpose]
                engine = FilterEngine({purpose: rule})
                filtered = []
                
                for photo in photos:
                    passes, score = engine.apply(photo, purpose)
                    if passes:
                        photo.match_scores[purpose] = score
                        filtered.append((photo, score))
                
                # Sort & limit
                filtered.sort(key=lambda x: x[1], reverse=True)
                top_n = rule.get('output', {}).get('top_n', len(filtered))
                filtered = filtered[:top_n]
                
                # Save
                if self.output_dir:
                    save_path = Path(self.output_dir) / purpose
                    save_path.mkdir(parents=True, exist_ok=True)
                    for photo, _ in filtered:
                        shutil.copy2(photo.path, save_path / photo.filename)
                
                results[purpose] = len(filtered)
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def _scan_photos(self, directory: Path) -> list:
        exts = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'}
        photos = []
        for ext in exts:
            photos.extend(directory.glob(f"*{ext}"))
            photos.extend(directory.glob(f"*{ext.upper()}"))
        return sorted(photos)
    
    def _process_photos(self, photo_files, analyzer, semantic_matcher):
        photos = []
        total = len(photo_files)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self._analyze_photo, f, analyzer, semantic_matcher): f for f in photo_files}
            completed = 0
            for future in concurrent.futures.as_completed(futures):
                photo = future.result()
                if photo:
                    photos.append(photo)
                completed += 1
                self.progress.emit(int(completed / total * 100))
        
        return photos
    
    def _analyze_photo(self, path, analyzer, semantic_matcher):
        photo = Photo(path=path, filename=path.name)
        photo = analyzer.analyze(photo)
        photo = analyzer.detect_faces(photo)
        
        if semantic_matcher:
            keywords = []
            for rule in self.config_data.values():
                if rule.get('semantic_matching', {}).get('enabled'):
                    keywords.extend(rule.get('semantic_matching', {}).get('keywords', []))
            if keywords:
                keywords = list(set(keywords))
                photo.clip_scores = semantic_matcher.match_photo(photo, keywords)
        
        return photo


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Filter - 智能照片筛选")
        self.setGeometry(100, 100, 800, 600)
        
        self.config_data = {}
        self.worker = None
        
        self._init_ui()
    
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Input section
        input_group = QGroupBox("输入输出")
        input_layout = QHBoxLayout()
        
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("输入目录")
        input_btn = QPushButton("浏览")
        input_btn.clicked.connect(self._browse_input)
        
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("输出目录")
        output_btn = QPushButton("浏览")
        output_btn.clicked.connect(self._browse_output)
        
        input_layout.addWidget(QLabel("输入:"))
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(input_btn)
        input_layout.addWidget(QLabel("输出:"))
        input_layout.addWidget(self.output_edit)
        input_layout.addWidget(output_btn)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Config section
        config_group = QGroupBox("配置文件")
        config_layout = QHBoxLayout()
        
        self.config_edit = QLineEdit()
        self.config_edit.setPlaceholderText("YAML配置文件")
        config_btn = QPushButton("浏览")
        config_btn.clicked.connect(self._browse_config)
        
        self.use_clip_cb = QCheckBox("启用CLIP语义匹配")
        
        config_layout.addWidget(QLabel("配置:"))
        config_layout.addWidget(self.config_edit)
        config_layout.addWidget(config_btn)
        config_layout.addWidget(self.use_clip_cb)
        config_layout.addStretch()
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Purposes
        purpose_group = QGroupBox("筛选目的")
        self.purpose_list = QListWidget()
        self.purpose_list.setSelectionMode(QListWidget.MultiSelection)
        purpose_layout = QVBoxLayout()
        purpose_layout.addWidget(self.purpose_list)
        purpose_group.setLayout(purpose_layout)
        layout.addWidget(purpose_group)
        
        # Workers
        worker_layout = QHBoxLayout()
        worker_layout.addWidget(QLabel("线程数:"))
        self.worker_slider = QSlider(Qt.Horizontal)
        self.worker_slider.setMinimum(1)
        self.worker_slider.setMaximum(8)
        self.worker_slider.setValue(4)
        self.worker_label = QLabel("4")
        self.worker_slider.valueChanged.connect(lambda v: self.worker_label.setText(str(v)))
        worker_layout.addWidget(self.worker_slider)
        worker_layout.addWidget(self.worker_label)
        worker_layout.addStretch()
        layout.addLayout(worker_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.status_edit = QTextEdit()
        self.status_edit.setReadOnly(True)
        self.status_edit.setMaximumHeight(100)
        layout.addWidget(self.status_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始筛选")
        self.start_btn.clicked.connect(self._start_filter)
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self._stop_filter)
        self.stop_btn.setEnabled(False)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)
    
    def _browse_input(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输入目录")
        if dir_path:
            self.input_edit.setText(dir_path)
    
    def _browse_output(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_edit.setText(dir_path)
    
    def _browse_config(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择配置文件", "", "YAML Files (*.yaml *.yml)"
        )
        if file_path:
            self.config_edit.setText(file_path)
            self._load_config(file_path)
    
    def _load_config(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.config_data = yaml.safe_load(f)
            
            # Update purpose list
            self.purpose_list.clear()
            for name, rule in self.config_data.items():
                if rule.get('enabled', True):
                    self.purpose_list.addItem(name)
            
            self._log(f"已加载配置: {path}")
            self._log(f"可用筛选目的: {', '.join(self.config_data.keys())}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载配置失败: {e}")
    
    def _start_filter(self):
        input_dir = self.input_edit.text()
        output_dir = self.output_edit.text()
        
        if not input_dir or not Path(input_dir).exists():
            QMessageBox.warning(self, "错误", "请选择有效的输入目录")
            return
        
        if not output_dir:
            QMessageBox.warning(self, "错误", "请选择输出目录")
            return
        
        # Get selected purposes
        selected = [item.text() for item in self.purpose_list.selectedItems()]
        if not selected:
            QMessageBox.warning(self, "错误", "请选择至少一个筛选目的")
            return
        
        # Load config if not loaded
        if not self.config_data:
            config_path = self.config_edit.text()
            if config_path and Path(config_path).exists():
                self._load_config(config_path)
        
        # Start worker
        use_clip = self.use_clip_cb.isChecked()
        workers = self.worker_slider.value()
        
        self.worker = FilterWorker(
            input_dir, output_dir, self.config_data, selected, use_clip, workers
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.status.connect(self._on_status)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        
        self.worker.start()
        self._log("开始筛选...")
    
    def _stop_filter(self):
        if self.worker:
            self.worker.terminate()
            self.worker.wait()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._log("已停止")
    
    def _on_progress(self, value):
        self.progress_bar.setValue(value)
    
    def _on_status(self, msg):
        self._log(msg)
    
    def _on_finished(self, results):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        msg = "筛选完成!\n\n"
        for purpose, count in results.items():
            msg += f"{purpose}: {count} 张\n"
        
        QMessageBox.information(self, "完成", msg)
        self._log("全部完成")
    
    def _on_error(self, err):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        QMessageBox.critical(self, "错误", err)
        self._log(f"错误: {err}")
    
    def _log(self, msg):
        self.status_edit.append(msg)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
