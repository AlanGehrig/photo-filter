"""Desktop GUI using PyQt5 - Optimized."""
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QProgressBar,
    QTextEdit, QComboBox, QCheckBox, QGroupBox, QScrollArea,
    QListWidget, QMessageBox, QSlider, QStatusBar, QToolBar,
    QAction, QShortcut, QFrame, QMenu, QDialog
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QIcon, QKeySequence, QPixmap, QImage

from photofilter.core import Photo, ImageAnalyzer, FilterEngine
# get_matcher 暂时禁用（PyTorch兼容性问题）
from photofilter.core.exif_tools import ExifReader, BatchRenamer
from photofilter.config import ConfigManager


class FilterWorker(QThread):
    """Background worker for photo filtering."""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, photos, filter_func, output_dir):
        super().__init__()
        self.photos = photos
        self.filter_func = filter_func
        self.output_dir = output_dir
        self.results = {"success": 0, "failed": 0, "skipped": 0}
    
    def run(self):
        total = len(self.photos)
        for i, photo in enumerate(self.photos):
            try:
                self.status.emit(f"处理: {photo.path.name}")
                result = self.filter_func(photo, self.output_dir)
                if result:
                    self.results["success"] += 1
                else:
                    self.results["skipped"] += 1
            except Exception as e:
                self.results["failed"] += 1
                self.error.emit(f"错误 {photo.path.name}: {e}")
            
            self.progress.emit(int((i + 1) / total * 100))
        
        self.finished.emit(self.results)


class AnalysisWorker(QThread):
    """Background worker for image analysis."""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, photos, analyzer):
        super().__init__()
        self.photos = photos
        self.analyzer = analyzer
    
    def run(self):
        total = len(self.photos)
        results = []
        
        for i, photo in enumerate(self.photos):
            try:
                self.status.emit(f"分析: {photo.path.name}")
                analyzed = self.analyzer.analyze(photo)
                results.append(analyzed)
            except Exception as e:
                self.error.emit(f"分析错误: {e}")
                results.append(photo)
            
            self.progress.emit(int((i + 1) / total * 100))
        
        self.finished.emit(results)


class SemanticWorker(QThread):
    """Background worker for semantic matching with batching."""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, photos, keywords, batch_size=8):
        super().__init__()
        self.photos = photos
        self.keywords = keywords
        self.batch_size = batch_size
    
    def run(self):
        if not self.keywords:
            self.finished.emit([])
            return
        
        try:
            self.status.emit("语义匹配功能暂时不可用（已禁用PyTorch）")
            self.finished.emit([])
            return
            
            total = len(self.photos)
            results = []
            
            # Use batch processing for speed
            for i in range(0, len(self.photos), self.batch_size):
                batch = self.photos[i:i + self.batch_size]
                batch_paths = [str(p.path) for p in batch]
                
                self.status.emit(f"语义匹配: {i+1}-{min(i+self.batch_size, total)}/{total}")
                
                try:
                    batch_results = matcher.match_batch(batch_paths, self.keywords, self.batch_size)
                    results.extend(batch_results)
                except Exception as e:
                    self.error.emit(f"匹配错误: {e}")
                    results.extend([{}] * len(batch))
                
                self.progress.emit(int(min(i + self.batch_size, total) / total * 100))
            
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(f"CLIP加载错误: {e}")
            self.finished.emit([])


class ThumbnailWorker(QThread):
    """Background worker for loading thumbnails."""
    finished = pyqtSignal(dict)
    
    def __init__(self, photos, size=64):
        super().__init__()
        self.photos = photos
        self.size = size
    
    def run(self):
        thumbnails = {}
        for photo in self.photos:
            try:
                pixmap = QPixmap(str(photo.path))
                scaled = pixmap.scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                thumbnails[str(photo.path)] = scaled
            except Exception:
                pass
        self.finished.emit(thumbnails)


class PhotoFilterGUI(QMainWindow):
    """Main application window - Optimized with background workers."""
    
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.photos = []
        self.filtered_photos = []
        self.output_dir = None
        self.semantic_results = {}
        self.thumbnails = {}  # Cache thumbnails
        
        # Initialize components
        self.analyzer = ImageAnalyzer()
        self.filter_engine = FilterEngine(self.config)
        self.exif_reader = ExifReader()
        self.batch_renamer = BatchRenamer()
        
        # Workers
        self.filter_worker = None
        self.analysis_worker = None
        self.semantic_worker = None
        self.thumbnail_worker = None
        
        self.init_ui()
        self.apply_theme()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+O"), self, self.open_folder)
        QShortcut(QKeySequence("F5"), self, self.refresh_photos)
        QShortcut(QKeySequence("Ctrl+A"), self, self.select_all_photos)
        QShortcut(QKeySequence("Delete"), self, self.delete_selected)
        QShortcut(QKeySequence("Return"), self, self.preview_selected)
        
        # Double-click to preview
        self.photo_list.itemDoubleClicked.connect(self.preview_photo)
    
    def init_ui(self):
        self.setWindowTitle("Photo Filter Pro 📷")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        open_action = QAction("📂 打开文件夹", self)
        open_action.triggered.connect(self.open_folder)
        toolbar.addAction(open_action)
        
        refresh_action = QAction("🔄 刷新", self)
        refresh_action.triggered.connect(self.refresh_photos)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        analyze_action = QAction("📊 分析图片", self)
        analyze_action.triggered.connect(self.analyze_photos)
        toolbar.addAction(analyze_action)
        
        match_action = QAction("🏷️ 语义匹配", self)
        match_action.triggered.connect(self.match_semantic)
        toolbar.addAction(match_action)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # Main content area
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)
        
        # Left panel - Controls
        left_panel = self.create_control_panel()
        content_layout.addWidget(left_panel, 1)
        
        # Right panel - Photo list
        right_panel = self.create_photo_panel()
        content_layout.addWidget(right_panel, 2)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
    
    # ===== Drag & Drop Support =====
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            folder = url.toLocalFile()
            if Path(folder).is_dir():
                self.folder_input.setText(folder)
                self.load_photos(Path(folder))
                break
    
    # ===== Right Click Menu =====
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        
        open_action = menu.addAction("📂 打开文件夹")
        open_action.triggered.connect(self.open_folder)
        
        refresh_action = menu.addAction("🔄 刷新")
        refresh_action.triggered.connect(self.refresh_photos)
        
        menu.addSeparator()
        
        select_all_action = menu.addAction("☑️ 全选")
        select_all_action.triggered.connect(self.select_all_photos)
        
        deselect_action = menu.addAction("☐ 取消全选")
        deselect_action.triggered.connect(self.photo_list.clearSelection)
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️ 删除选中")
        delete_action.triggered.connect(self.delete_selected)
        
        reveal_action = menu.addAction("📍 打开所在位置")
        reveal_action.triggered.connect(self.reveal_in_explorer)
        
        menu.exec_(event.globalPos())
    
    def create_control_panel(self) -> QWidget:
        """Create control panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Folder selection
        folder_group = QGroupBox("📁 文件夹")
        folder_layout = QVBoxLayout()
        
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("选择照片文件夹...")
        self.folder_input.setReadOnly(True)
        
        folder_btn_layout = QHBoxLayout()
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.open_folder)
        
        output_btn = QPushButton("输出到...")
        output_btn.clicked.connect(self.select_output_dir)
        
        folder_btn_layout.addWidget(browse_btn)
        folder_btn_layout.addWidget(output_btn)
        
        folder_layout.addWidget(self.folder_input)
        folder_layout.addLayout(folder_btn_layout)
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)
        
        # Filters
        filter_group = QGroupBox("🔍 筛选条件")
        filter_layout = QVBoxLayout()
        
        # Format filter
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["全部", "jpg", "png", "webp", "raw"])
        format_layout.addWidget(self.format_combo)
        filter_layout.addLayout(format_layout)
        
        # Size filter
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("最小尺寸:"))
        self.min_size_slider = QSlider(Qt.Horizontal)
        self.min_size_slider.setMinimum(0)
        self.min_size_slider.setMaximum(20)
        self.min_size_slider.setValue(0)
        self.min_size_label = QLabel("0 MB")
        self.min_size_slider.valueChanged.connect(
            lambda v: self.min_size_label.setText(f"{v} MB")
        )
        size_layout.addWidget(self.min_size_slider)
        size_layout.addWidget(self.min_size_label)
        filter_layout.addLayout(size_layout)
        
        # Quality filters
        self.blur_check = QCheckBox("模糊图片")
        self.exposure_check = QCheckBox("曝光异常")
        self.face_check = QCheckBox("含人脸")
        filter_layout.addWidget(self.blur_check)
        filter_layout.addWidget(self.exposure_check)
        filter_layout.addWidget(self.face_check)
        
        # Semantic matching
        semantic_layout = QVBoxLayout()
        semantic_layout.addWidget(QLabel("🏷️ 语义标签 (逗号分隔):"))
        self.keywords_input = QLineEdit()
        self.keywords_input.setPlaceholderText("例如: 风景, 人物, 美食")
        semantic_layout.addWidget(self.keywords_input)
        
        match_btn = QPushButton("执行语义匹配")
        match_btn.clicked.connect(self.match_semantic)
        semantic_layout.addWidget(match_btn)
        
        filter_layout.addLayout(semantic_layout)
        
        # Apply filters button
        apply_btn = QPushButton("✅ 应用筛选")
        apply_btn.clicked.connect(self.apply_filters)
        filter_layout.addWidget(apply_btn)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Processing
        process_group = QGroupBox("⚙️ 处理")
        process_layout = QVBoxLayout()
        
        self.process_btn = QPushButton("🚀 开始处理")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        process_layout.addWidget(self.process_btn)
        
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)
        
        # Log
        log_group = QGroupBox("📋 日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Batch rename
        rename_group = QGroupBox("📝 批量重命名")
        rename_layout = QVBoxLayout()
        
        self.rename_pattern = QLineEdit()
        self.rename_pattern.setPlaceholderText("例如: photo_{n:03d}_{date}")
        rename_layout.addWidget(QLabel("命名规则:"))
        rename_layout.addWidget(self.rename_pattern)
        
        rename_btn_layout = QHBoxLayout()
        preview_rename_btn = QPushButton("👁️ 预览")
        preview_rename_btn.clicked.connect(self.preview_rename)
        
        apply_rename_btn = QPushButton("✅ 执行重命名")
        apply_rename_btn.clicked.connect(self.apply_rename)
        
        rename_btn_layout.addWidget(preview_rename_btn)
        rename_btn_layout.addWidget(apply_rename_btn)
        rename_layout.addLayout(rename_btn_layout)
        
        rename_group.setLayout(rename_layout)
        layout.addWidget(rename_group)
        
        layout.addStretch()
        return widget
    
    def create_photo_panel(self) -> QWidget:
        """Create photo list panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header_layout = QHBoxLayout()
        self.photo_count_label = QLabel("0 张照片")
        header_layout.addWidget(self.photo_count_label)
        
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self.select_all_photos)
        header_layout.addWidget(select_all_btn)
        
        layout.addLayout(header_layout)
        
        # Photo list
        self.photo_list = QListWidget()
        self.photo_list.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(self.photo_list)
        
        return widget
    
    def apply_theme(self):
        """Apply modern dark theme."""
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QWidget { color: #e0e0e0; background-color: #1e1e1e; }
            QGroupBox {
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QPushButton {
                background-color: #3a3a3a;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                color: white;
            }
            QPushButton:hover { background-color: #4a4a4a; }
            QPushButton:pressed { background-color: #2a2a2a; }
            QPushButton:disabled { background-color: #2a2a2a; color: #666; }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 5px;
            }
            QProgressBar {
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                text-align: center;
                background-color: #2a2a2a;
            }
            QProgressBar::chunk { background-color: #4CAF50; }
            QListWidget { background-color: #2a2a2a; border: 1px solid #3a3a3a; }
            QListWidget::item:selected { background-color: #4CAF50; }
            QStatusBar { background-color: #2a2a2a; }
            QCheckBox { spacing: 8px; }
            QCheckBox::indicator { width: 18px; height: 18px; }
        """)
    
    def log(self, message: str):
        """Add message to log."""
        self.log_text.append(message)
        self.status_bar.showMessage(message)
    
    def open_folder(self):
        """Open folder dialog."""
        folder = QFileDialog.getExistingDirectory(self, "选择照片文件夹")
        if folder:
            self.folder_input.setText(folder)
            self.load_photos(Path(folder))
    
    def select_output_dir(self):
        """Select output directory."""
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_dir = Path(folder)
            self.log(f"输出目录: {self.output_dir}")
    
    def load_photos(self, folder: Path):
        """Load photos from folder."""
        self.photos = []
        extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.raw'}
        
        for ext in extensions:
            for path in folder.glob(f"*{ext}"):
                self.photos.append(Photo(path))
            for path in folder.glob(f"*{ext.upper()}"):
                self.photos.append(Photo(path))
        
        self.filtered_photos = self.photos.copy()
        self.update_photo_list()
        self.log(f"加载了 {len(self.photos)} 张照片")
    
    def refresh_photos(self):
        """Refresh photo list."""
        folder = self.folder_input.text()
        if folder:
            self.load_photos(Path(folder))
    
    def update_photo_list(self):
        """Update photo list widget."""
        self.photo_list.clear()
        for photo in self.filtered_photos:
            self.photo_list.addItem(photo.path.name)
        self.photo_count_label.setText(f"{len(self.filtered_photos)} 张照片")
    
    def select_all_photos(self):
        """Select all photos."""
        self.photo_list.selectAll()
    
    def apply_filters(self):
        """Apply filters to photos."""
        if not self.photos:
            return
        
        self.filtered_photos = self.photos.copy()
        
        # Format filter
        fmt = self.format_combo.currentText()
        if fmt != "全部":
            self.filtered_photos = [p for p in self.filtered_photos if p.path.suffix[1:].lower() == fmt.lower()]
        
        # Size filter
        min_size_mb = self.min_size_slider.value()
        if min_size_mb > 0:
            min_bytes = min_size_mb * 1024 * 1024
            self.filtered_photos = [p for p in self.filtered_photos if p.path.stat().st_size >= min_bytes]
        
        # Quality filters (if analyzed)
        if self.blur_check.isChecked():
            self.filtered_photos = [p for p in self.filtered_photos if getattr(p, 'blur_score', 0) < 100]
        
        if self.exposure_check.isChecked():
            self.filtered_photos = [p for p in self.filtered_photos 
                if getattr(p, 'is_overexposed', False) or getattr(p, 'is_underexposed', False)]
        
        if self.face_check.isChecked():
            self.filtered_photos = [p for p in self.filtered_photos if getattr(p, 'has_face', False)]
        
        # Semantic filter
        if self.semantic_results and self.keywords_input.text():
            keywords = [k.strip() for k in self.keywords_input.text().split(',')]
            self.filtered_photos = [p for p in self.filtered_photos 
                if str(p.path) in self.semantic_results]
        
        self.update_photo_list()
        self.log(f"筛选后: {len(self.filtered_photos)} 张照片")
        
        # Enable process button
        self.process_btn.setEnabled(len(self.filtered_photos) > 0 and self.output_dir is not None)
    
    def analyze_photos(self):
        """Analyze selected photos in background."""
        if not self.photos:
            return
        
        self.log("开始分析图片...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.analysis_worker = AnalysisWorker(self.photos, self.analyzer)
        self.analysis_worker.progress.connect(self.progress_bar.setValue)
        self.analysis_worker.status.connect(self.log)
        self.analysis_worker.finished.connect(self.on_analysis_finished)
        self.analysis_worker.error.connect(self.log)
        self.analysis_worker.start()
    
    def on_analysis_finished(self, results):
        """Handle analysis completion."""
        self.photos = results
        self.log("图片分析完成")
        self.progress_bar.setVisible(False)
        
        # Show summary
        blur_count = sum(1 for p in self.photos if getattr(p, 'blur_score', 0) < 100)
        over_count = sum(1 for p in self.photos if getattr(p, 'is_overexposed', False))
        under_count = sum(1 for p in self.photos if getattr(p, 'is_underexposed', False))
        
        self.log(f"📊 分析结果: 模糊 {blur_count}, 过曝 {over_count}, 欠曝 {under_count}")
    
    def match_semantic(self):
        """Perform semantic matching in background."""
        if not self.photos:
            return
        
        keywords_text = self.keywords_input.text().strip()
        if not keywords_text:
            self.log("请输入语义标签")
            return
        
        keywords = [k.strip() for k in keywords_text.split(',')]
        if not keywords:
            return
        
        self.log(f"开始语义匹配: {keywords}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.semantic_worker = SemanticWorker(self.photos, keywords)
        self.semantic_worker.progress.connect(self.progress_bar.setValue)
        self.semantic_worker.status.connect(self.log)
        self.semantic_worker.finished.connect(self.on_semantic_finished)
        self.semantic_worker.error.connect(self.log)
        self.semantic_worker.start()
    
    def on_semantic_finished(self, results):
        """Handle semantic matching completion."""
        self.progress_bar.setVisible(False)
        
        # Store results
        self.semantic_results = {}
        for i, photo in enumerate(self.photos):
            if i < len(results):
                self.semantic_results[str(photo.path)] = results[i]
        
        self.log("语义匹配完成")
        
        # Show top matches
        for kw in results[0].keys() if results else []:
            scores = [(str(p.path), r.get(kw, 0)) for p, r in zip(self.photos, results) if r]
            scores.sort(key=lambda x: x[1], reverse=True)
            top3 = scores[:3]
            self.log(f"'{kw}' 最高匹配: {[Path(p).name for p, s in top3]}")
    
    def start_processing(self):
        """Start filtering process in background."""
        if not self.filtered_photos or not self.output_dir:
            return
        
        self.log(f"开始处理 {len(self.filtered_photos)} 张照片...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.filter_worker = FilterWorker(
            self.filtered_photos,
            self.filter_engine.apply_filters,
            self.output_dir
        )
        self.filter_worker.progress.connect(self.progress_bar.setValue)
        self.filter_worker.status.connect(self.log)
        self.filter_worker.finished.connect(self.on_processing_finished)
        self.filter_worker.error.connect(self.log)
        self.filter_worker.start()
    
    def on_processing_finished(self, results):
        """Handle processing completion."""
        self.progress_bar.setVisible(False)
        self.log(f"处理完成! 成功: {results['success']}, 失败: {results['failed']}, 跳过: {results['skipped']}")
        
        QMessageBox.information(self, "完成", 
            f"处理完成!\n成功: {results['success']}\n失败: {results['failed']}\n跳过: {results['skipped']}")
    
    # ===== New Features =====
    def delete_selected(self):
        """Delete selected photos (move to recycle bin)."""
        selected = self.photo_list.selectedIndexes()
        if not selected:
            return
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"将 {len(selected)} 张照片移到回收站?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            count = 0
            for idx in selected:
                photo = self.filtered_photos[idx.row()]
                try:
                    # Move to recycle bin
                    import winshell
                    winshell.delete_file(str(photo.path), allow_undo=True, silent=True)
                    count += 1
                except Exception as e:
                    self.log(f"删除失败: {photo.path.name} - {e}")
            
            self.log(f"已删除 {count} 张照片")
            self.refresh_photos()
    
    def reveal_in_explorer(self):
        """Open file location in Explorer."""
        selected = self.photo_list.selectedIndexes()
        if not selected:
            return
        
        photo = self.filtered_photos[selected[0].row()]
        import os
        os.startfile(str(photo.path.parent))
    
    def preview_photo(self, item):
        """Preview selected photo with EXIF info."""
        row = self.photo_list.row(item)
        if row >= len(self.filtered_photos):
            return
        
        photo = self.filtered_photos[row]
        
        # Read EXIF
        exif = self.exif_reader.read(photo)
        
        dialog = QDialog(self)
        dialog.setWindowTitle(photo.path.name)
        dialog.setMinimumSize(800, 650)
        layout = QVBoxLayout(dialog)
        
        # Image
        pixmap = QPixmap(str(photo.path))
        scaled = pixmap.scaled(750, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label = QLabel()
        label.setPixmap(scaled)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # EXIF Info
        info_text = f"""
<b>📷 照片信息</b><br>
━━━━━━━━━━━━━━━━━━━<br>
<b>文件名:</b> {photo.path.name}<br>
<b>尺寸:</b> {photo.width} x {photo.height}<br>
<b>大小:</b> {photo.size_bytes/1024/1024:.2f} MB<br>
"""
        
        if exif.get('exists'):
            info_text += f"""
<b>📅 拍摄时间:</b> {exif.get('date_taken', 'N/A')}<br>
<b>📷 相机:</b> {exif.get('camera', 'N/A')}<br>
<b>🔭 焦距:</b> {exif.get('focal', 'N/A')}<br>
<b>📸 光圈:</b> {exif.get('aperture', 'N/A')}<br>
<b>⏱️ 快门:</b> {exif.get('shutter', 'N/A')}<br>
<b>🔆 ISO:</b> {exif.get('iso', 'N/A')}<br>
"""
        
        info = QLabel(info_text)
        info.setTextFormat(Qt.RichText)
        info.setAlignment(Qt.AlignLeft)
        layout.addWidget(info)
        
        # Buttons
        btn_layout = QHBoxLayout()
        open_btn = QPushButton("📍 打开位置")
        open_btn.clicked.connect(lambda: self.reveal_in_explorer())
        
        # Add to rename pattern
        if exif.get('date_taken'):
            date_str = exif.get('date_taken', '')[:10].replace(':', '')
            add_date_btn = QPushButton("📅 加日期到重命名")
            add_date_btn.clicked.connect(lambda: self.rename_pattern.setText(f"photo_{{n:03d}}_{date_str}"))
            btn_layout.addWidget(add_date_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        
        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    
    def load_thumbnails(self):
        """Load thumbnails in background."""
        if self.thumbnail_worker and self.thumbnail_worker.isRunning():
            return
        
        self.thumbnail_worker = ThumbnailWorker(self.filtered_photos)
        self.thumbnail_worker.finished.connect(self.on_thumbnails_loaded)
        self.thumbnail_worker.start()
    
    def on_thumbnails_loaded(self, thumbnails):
        """Update list with thumbnails."""
        self.thumbnails = thumbnails
        for i in range(self.photo_list.count()):
            item = self.photo_list.item(i)
            path = self.filtered_photos[i].path
            if str(path) in thumbnails:
                icon = QIcon(thumbnails[str(path)])
                item.setIcon(icon)
    
    def preview_selected(self):
        """Preview currently selected photo."""
        selected = self.photo_list.selectedIndexes()
        if selected:
            self.preview_photo(self.photo_list.item(selected[0].row()))
    
    def preview_rename(self):
        """Preview batch rename."""
        if not self.filtered_photos:
            self.log("没有可重命名的照片")
            return
        
        pattern = self.rename_pattern.text().strip()
        if not pattern:
            self.log("请输入命名规则")
            return
        
        self.log(f"预览重命名 ({len(self.filtered_photos)} 张)...")
        
        preview = self.batch_renamer.preview(
            self.filtered_photos[:20],  # Preview first 20
            pattern
        )
        
        self.log("=== 预览前 20 个 ===")
        for item in preview:
            self.log(f"  {item['original']} → {item['new']}")
        
        if len(self.filtered_photos) > 20:
            self.log(f"  ... 还有 {len(self.filtered_photos) - 20} 个")
    
    def apply_rename(self):
        """Execute batch rename."""
        if not self.filtered_photos:
            self.log("没有可重命名的照片")
            return
        
        pattern = self.rename_pattern.text().strip()
        if not pattern:
            self.log("请输入命名规则")
            return
        
        reply = QMessageBox.question(
            self, "确认重命名",
            f"将 {len(self.filtered_photos)} 张照片重命名?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.log("执行重命名...")
            result = self.batch_renamer.execute(self.filtered_photos, pattern)
            
            self.log(f"完成! 成功: {result['success']}, 失败: {result['failed']}")
            
            for err in result['errors'][:5]:
                self.log(f"  错误: {err}")
            
            # Refresh list
            self.refresh_photos()


def main():
    app = QApplication(sys.argv)
    window = PhotoFilterGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
