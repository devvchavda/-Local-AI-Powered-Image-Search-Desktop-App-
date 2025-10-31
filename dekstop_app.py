"""
Modern Image Search Desktop App — PySide6
Minimalist full-scale design inspired by Claude
Features:
 - Clean, minimal UI with no headers/dashboard
 - Real-time search suggestions as you type
 - Pan and zoom image preview
 - Non-blocking threaded operations
 - Elegant dark theme
Dependencies:
    pip install PySide6 Pillow
"""

import sys
import os
import threading
import traceback
from typing import List
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QFileDialog, QMessageBox,
    QProgressBar, QSplitter, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QFrame
)
from PySide6.QtGui import QPixmap, QIcon, QWheelEvent, QPainter
from PySide6.QtCore import Qt, QSize, Signal, QObject, QTimer

# === Import your backend ===
from image_search import ImageSearcher


# ---------- Helpers ----------
def load_pixmap(path: str, max_size: QSize) -> QPixmap:
    pix = QPixmap(path)
    if pix.isNull():
        return QPixmap()
    return pix.scaled(max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(int)


# ---------- Thread Workers ----------
class SearchWorker(threading.Thread):
    def __init__(self, searcher, query: str, signals: WorkerSignals):
        super().__init__(daemon=True)
        self.searcher = searcher
        self.query = query
        self.signals = signals

    def run(self):
        try:
            res = self.searcher.search(self.query, show=False)
            paths = []
            for item in res:
                if hasattr(item, 'metadata') and isinstance(item.metadata, dict):
                    p = item.metadata.get('path')
                    if p:
                        paths.append(p)
                elif isinstance(item, str):
                    paths.append(item)
            self.signals.finished.emit(paths)
        except Exception:
            self.signals.error.emit(traceback.format_exc())


class AddWorker(threading.Thread):
    def __init__(self, searcher, paths: List[str], signals: WorkerSignals):
        super().__init__(daemon=True)
        self.searcher = searcher
        self.paths = paths
        self.signals = signals

    def run(self):
        try:
            added = 0
            total = len(self.paths)
            for i, p in enumerate(self.paths, start=1):
                if os.path.isdir(p):
                    self.searcher.process_dir(p)
                    added += 1
                else:
                    if hasattr(self.searcher.imagedocs, 'create_documents'):
                        caps, meta = self.searcher.imagedocs.create_documents(p)
                        self.searcher.vecstore.add_documents(caps, meta)
                        added += 1
                    else:
                        parent = os.path.dirname(p)
                        self.searcher.process_dir(parent)
                        added += 1
                self.signals.progress.emit(int(i / total * 100))
            self.signals.finished.emit(added)
        except Exception:
            self.signals.error.emit(traceback.format_exc())


# ---------- Pannable + Zoomable Preview ----------
class PannableImageView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(Qt.black)
        self._pixmap_item = None
        self._zoom = 1.0
        self._current_pixmap = None

    def set_image(self, path: str):
        self.scene.clear()
        pix = QPixmap(path)
        if pix.isNull():
            return
        self._current_pixmap = pix
        self._pixmap_item = QGraphicsPixmapItem(pix)
        self.scene.addItem(self._pixmap_item)
        self._zoom = 1.0
        self.fit_to_window()

    def wheelEvent(self, e: QWheelEvent):
        if e.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        self._zoom *= 1.15
        self.scale(1.15, 1.15)

    def zoom_out(self):
        self._zoom /= 1.15
        self.scale(1 / 1.15, 1 / 1.15)

    def reset_zoom(self):
        self.resetTransform()
        self._zoom = 1.0

    def fit_to_window(self):
        if self._pixmap_item:
            self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)
            self._zoom = self.transform().m11()


# ---------- Main Application ----------
class ImageSearchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Search")
        self.setMinimumSize(1400, 800)
        self.searcher = ImageSearcher()
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)

        self._build_ui()
        self._apply_minimal_theme()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Main content splitter (full height)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(1)
        
        # Left panel - Results
        left_panel = QWidget()
        left_panel.setObjectName("leftPanel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # Search bar at top of left panel
        search_container = QWidget()
        search_container.setObjectName("searchContainer")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(20, 20, 20, 20)
        search_layout.setSpacing(10)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search images...")
        self.search_box.setObjectName("searchInput")
        self.search_box.textChanged.connect(self.on_text_changed)
        search_layout.addWidget(self.search_box)
        
        add_btn = QPushButton("➕")
        add_btn.setObjectName("toolBtn")
        add_btn.setToolTip("Add Images")
        add_btn.clicked.connect(self.on_add_images)
        search_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("🗑️")
        remove_btn.setObjectName("toolBtn")
        remove_btn.setToolTip("Remove Selected")
        remove_btn.clicked.connect(self.on_remove_selected)
        search_layout.addWidget(remove_btn)
        
        left_layout.addWidget(search_container)
        
        # Results list
        self.results = QListWidget()
        self.results.setObjectName("resultsList")
        self.results.setIconSize(QSize(200, 150))
        self.results.setSpacing(10)
        self.results.itemSelectionChanged.connect(self.on_result_selected)
        left_layout.addWidget(self.results)
        
        # Status bar at bottom of left panel
        status_widget = QWidget()
        status_widget.setObjectName("statusBar")
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(20, 12, 20, 12)
        
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusText")
        status_layout.addWidget(self.status_label)
        
        self.progress = QProgressBar()
        self.progress.setObjectName("progressBar")
        self.progress.setVisible(False)
        self.progress.setMaximumWidth(200)
        self.progress.setMaximumHeight(4)
        self.progress.setTextVisible(False)
        status_layout.addWidget(self.progress)
        
        left_layout.addWidget(status_widget)
        
        self.splitter.addWidget(left_panel)

        # Right panel - Preview
        right_panel = QWidget()
        right_panel.setObjectName("rightPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Toolbar for zoom controls
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(20, 15, 20, 15)
        toolbar_layout.addStretch()
        
        btn_in = QPushButton("Zoom In")
        btn_out = QPushButton("Zoom Out")
        btn_fit = QPushButton("Fit")
        btn_reset = QPushButton("Reset")
        
        for b in [btn_in, btn_out, btn_fit, btn_reset]:
            b.setObjectName("zoomBtn")
            toolbar_layout.addWidget(b)
        
        right_layout.addWidget(toolbar)
        
        # Image preview
        self.preview = PannableImageView()
        self.preview.setObjectName("imagePreview")
        right_layout.addWidget(self.preview)
        
        btn_in.clicked.connect(self.preview.zoom_in)
        btn_out.clicked.connect(self.preview.zoom_out)
        btn_fit.clicked.connect(self.preview.fit_to_window)
        btn_reset.clicked.connect(self.preview.reset_zoom)
        
        self.splitter.addWidget(right_panel)
        
        # Set initial splitter sizes (30% left, 70% right)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 7)
        
        main_layout.addWidget(self.splitter)

    def _apply_minimal_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #e0e0e0;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 14px;
            }
            
            #leftPanel {
                background-color: #1a1a1a;
                border-right: 1px solid #2d2d2d;
            }
            
            #rightPanel {
                background-color: #0d0d0d;
            }
            
            #searchContainer {
                background-color: #1a1a1a;
                border-bottom: 1px solid #2d2d2d;
            }
            
            #searchInput {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 15px;
                color: #ffffff;
            }
            
            #searchInput:focus {
                border: 2px solid #5d5d5d;
                background-color: #333333;
            }
            
            #toolBtn {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 16px;
                min-width: 45px;
                max-width: 45px;
            }
            
            #toolBtn:hover {
                background-color: #3d3d3d;
                border: 1px solid #4d4d4d;
            }
            
            #toolBtn:pressed {
                background-color: #252525;
            }
            
            #resultsList {
                background-color: #1a1a1a;
                border: none;
                padding: 15px;
                outline: none;
            }
            
            #resultsList::item {
                background-color: #252525;
                border: 1px solid #2d2d2d;
                border-radius: 12px;
                padding: 12px;
                margin: 5px 0;
            }
            
            #resultsList::item:hover {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
            }
            
            #resultsList::item:selected {
                background-color: #3d3d3d;
                border: 1px solid #5d5d5d;
            }
            
            #toolbar {
                background-color: #0d0d0d;
                border-bottom: 1px solid #2d2d2d;
            }
            
            #zoomBtn {
                background-color: #252525;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 8px 16px;
                color: #e0e0e0;
                font-size: 13px;
                font-weight: 500;
            }
            
            #zoomBtn:hover {
                background-color: #2d2d2d;
                border: 1px solid #4d4d4d;
            }
            
            #zoomBtn:pressed {
                background-color: #1d1d1d;
            }
            
            #imagePreview {
                background-color: #000000;
                border: none;
            }
            
            #statusBar {
                background-color: #1a1a1a;
                border-top: 1px solid #2d2d2d;
            }
            
            #statusText {
                color: #a0a0a0;
                font-size: 13px;
            }
            
            #progressBar {
                border: none;
                border-radius: 2px;
                background-color: #2d2d2d;
            }
            
            #progressBar::chunk {
                background-color: #5d5d5d;
                border-radius: 2px;
            }
            
            QSplitter::handle {
                background-color: #2d2d2d;
            }
            
            QSplitter::handle:hover {
                background-color: #3d3d3d;
            }
            
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 12px;
                border: none;
            }
            
            QScrollBar::handle:vertical {
                background-color: #3d3d3d;
                border-radius: 6px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #4d4d4d;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            
            QMessageBox {
                background-color: #2d2d2d;
            }
            
            QMessageBox QLabel {
                color: #e0e0e0;
            }
            
            QMessageBox QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #4d4d4d;
                border-radius: 6px;
                padding: 8px 20px;
                color: #e0e0e0;
                min-width: 80px;
            }
            
            QMessageBox QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)

    # ---------- Handlers ----------
    def on_text_changed(self):
        self.search_timer.stop()
        query = self.search_box.text().strip()
        if len(query) >= 2:
            self.search_timer.start(300)
        elif not query:
            self.results.clear()
            self.status_label.setText("Ready")

    def _perform_search(self):
        query = self.search_box.text().strip()
        if not query:
            return
        
        self.results.clear()
        self.progress.setVisible(True)
        self.status_label.setText(f"Searching for '{query}'...")

        signals = WorkerSignals()
        signals.finished.connect(self.on_search_finished)
        signals.error.connect(self.on_search_error)

        worker = SearchWorker(self.searcher, query, signals)
        worker.start()

    def on_search_finished(self, paths: List[str]):
        self.progress.setVisible(False)
        self.status_label.setText(f"Found {len(paths)} results")
        
        for p in paths:
            if not os.path.exists(p):
                continue
            item = QListWidgetItem(os.path.basename(p))
            pix = load_pixmap(p, QSize(200, 150))
            if not pix.isNull():
                item.setIcon(QIcon(pix))
            item.setData(Qt.UserRole, p)
            self.results.addItem(item)

    def on_search_error(self, tb: str):
        self.progress.setVisible(False)
        self.status_label.setText("Search error occurred")
        QMessageBox.critical(self, "Search Error", tb)

    def on_result_selected(self):
        items = self.results.selectedItems()
        if not items:
            return
        path = items[0].data(Qt.UserRole)
        if not os.path.exists(path):
            self.status_label.setText("File not found")
            return
        self.preview.set_image(path)
        self.status_label.setText(f"Viewing: {os.path.basename(path)}")

    def on_add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select images", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if not files:
            return
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status_label.setText(f"Adding {len(files)} images...")
        
        signals = WorkerSignals()
        signals.finished.connect(self.on_add_finished)
        signals.error.connect(self.on_add_error)
        signals.progress.connect(lambda v: self.progress.setValue(v))

        worker = AddWorker(self.searcher, files, signals)
        worker.start()

    def on_add_finished(self, added: int):
        self.progress.setVisible(False)
        self.status_label.setText(f"Added {added} images")
        QMessageBox.information(self, "Success", f"Successfully added {added} images!")

    def on_add_error(self, tb: str):
        self.progress.setVisible(False)
        self.status_label.setText("Error adding images")
        QMessageBox.critical(self, "Add Error", tb)

    def on_remove_selected(self):
        items = self.results.selectedItems()
        if not items:
            QMessageBox.information(self, "No Selection", "Please select an image to remove.")
            return
        path = items[0].data(Qt.UserRole)
        confirm = QMessageBox.question(
            self, "Confirm Removal", 
            f"Remove '{os.path.basename(path)}' from the index?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            if hasattr(self.searcher, "remove_image"):
                self.searcher.remove_image(path)
            elif hasattr(self.searcher, "remove_documents"):
                self.searcher.remove_documents(path)
            elif hasattr(self.searcher.vecstore, "remove_documents"):
                self.searcher.vecstore.remove_documents(path)
            self.results.takeItem(self.results.row(items[0]))
            self.status_label.setText("Image removed")
        except Exception as e:
            QMessageBox.critical(self, "Remove Error", str(e))
            self.status_label.setText("Failed to remove image")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = ImageSearchApp()
    win.show()
    sys.exit(app.exec())