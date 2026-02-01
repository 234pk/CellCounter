import os
import sys
import numpy as np
from datetime import datetime
from typing import List, Optional, Tuple

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFileDialog, QSpinBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QProgressBar, QMessageBox,
    QSplitter, QComboBox, QTabWidget, QToolBar, QSizePolicy, QFrame,
    QScrollArea, QButtonGroup
)
from PyQt6.QtCore import Qt, QPointF, QSettings
from PyQt6.QtGui import QAction, QKeySequence, QFont

from gui.viewer import PolygonViewer
from gui.styles import MAIN_STYLE
from core.detector import create_blob_detector, detect_cells_in_roi
from core.calculator import calculate_concentration
from core.utils import cv2_imread, cv2_imwrite, natural_sort_key

class CellCounterGUI(QMainWindow):
    """Hemocytometer Main GUI v2.1 - Refactored"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔬 Hemocytometer Cell Counter v2.1")
        
        # Initialize all UI attributes to None to avoid early signal crashes
        self.status_images = None
        self.status_polygons = None
        self.btn_roi_mode = None
        self.btn_manual_mode = None
        self.result_table = None
        self.spin_min_area = None
        self.spin_max_area = None
        self.chk_circularity = None
        self.spin_circularity = None
        self.combo_chamber = None
        self.spin_dilution = None
        self.combo_region = None
        self.spin_volume = None
        self.spin_total_vol = None
        self.btn_count = None
        self.btn_count_main = None
        self.btn_save_report = None
        self.conc_label = None
        self.total_sample_label = None
        self.progress_bar = None
        
        # UI Adaptation: Use screen geometry to set reasonable initial size
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.8)
        height = int(screen.height() * 0.8)
        self.resize(width, height)
        
        # Minimum size to ensure usability
        self.setMinimumSize(1024, 720)
        
        self.settings = QSettings("CellCounter", "Settings")
        self.image_paths: List[Optional[str]] = [None] * 4
        self.cell_counts: List[int] = [0] * 4
        self.results_dir = None
        self.detection_results = [None] * 4
        
        # Initialize last_dir before setup_ui to avoid AttributeError
        self.last_dir = self.settings.value("last_dir", os.path.expanduser("~"))
        
        self._setup_statusbar()
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self.setStyleSheet(MAIN_STYLE)
        self._setup_shortcuts()
        self._load_settings()

    def _load_settings(self):
        """Load saved parameters from QSettings"""
        self.spin_min_area.setValue(int(self.settings.value("min_area", 20)))
        self.spin_max_area.setValue(int(self.settings.value("max_area", 1000)))
        
        circ_idx = self.settings.value("circularity_enabled", "Enabled")
        self.chk_circularity.setCurrentText(circ_idx)
        self.spin_circularity.setValue(int(self.settings.value("min_circularity", 40)))
        
        self.combo_chamber.setCurrentText(self.settings.value("chamber", "Improved Neubauer (Standard)"))
        self.spin_dilution.setValue(float(self.settings.value("dilution", 1.0)))
        self.combo_region.setCurrentText(self.settings.value("region", "4 Corners (Animal Cells)"))
        self.spin_volume.setValue(float(self.settings.value("volume", 0.0001)))
        self.spin_total_vol.setValue(float(self.settings.value("total_volume", 1.0)))

    def _save_settings(self):
        """Save current parameters to QSettings"""
        self.settings.setValue("min_area", self.spin_min_area.value())
        self.settings.setValue("max_area", self.spin_max_area.value())
        self.settings.setValue("circularity_enabled", self.chk_circularity.currentText())
        self.settings.setValue("min_circularity", self.spin_circularity.value())
        self.settings.setValue("chamber", self.combo_chamber.currentText())
        self.settings.setValue("dilution", self.spin_dilution.value())
        self.settings.setValue("region", self.combo_region.currentText())
        self.settings.setValue("volume", self.spin_volume.value())
        self.settings.setValue("total_volume", self.spin_total_vol.value())
        self.settings.setValue("last_dir", self.last_dir)
    
    def _setup_shortcuts(self):
        # File/System
        QAction("Import", self, shortcut=QKeySequence("Ctrl+O"), triggered=self._import_images)
        QAction("Save", self, shortcut=QKeySequence("Ctrl+S"), triggered=self._save_results)
        QAction("Count", self, shortcut=QKeySequence("F5"), triggered=self._start_counting)
        
        # Edit/Mode
        QAction("Undo", self, shortcut=QKeySequence("Ctrl+Z"), triggered=self._undo_last_point)
        QAction("Clear Current", self, shortcut=QKeySequence("Delete"), triggered=self._clear_polygons)
        QAction("Toggle Mode", self, shortcut=QKeySequence("M"), triggered=self._shortcut_toggle_mode)
        
        # View
        QAction("Reset View", self, shortcut=QKeySequence("Ctrl+R"), triggered=self._reset_current_view)
        
        # Tab Switching (1-4)
        for i in range(4):
            QAction(f"Tab {i+1}", self, shortcut=QKeySequence(str(i+1)), 
                    triggered=lambda checked=False, idx=i: self.image_tabs.setCurrentIndex(idx))

    def _reset_current_view(self):
        self.viewers[self.image_tabs.currentIndex()].reset_view()

    def _shortcut_toggle_mode(self):
        self.btn_mode.toggle()
        self._toggle_mode()
    
    def _setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        title_label = QLabel(" 🔬 CellCounter v2.1 ")
        title_label.setStyleSheet("color: #00d4ff; font-weight: bold; font-size: 16px; margin-right: 15px;")
        toolbar.addWidget(title_label)
        toolbar.addSeparator()
        
        btn_import = QPushButton("📁 Import Images")
        btn_import.setFixedSize(130, 32)
        btn_import.clicked.connect(self._import_images)
        toolbar.addWidget(btn_import)
        toolbar.addSeparator()

        mode_label = QLabel(" Interaction Mode: ")
        mode_label.setStyleSheet("color: #888; font-weight: bold; margin-left: 10px;")
        toolbar.addWidget(mode_label)

        # Two distinct buttons for mode selection
        mode_group = QButtonGroup(self)
        
        self.btn_roi_mode = QPushButton("📐 ROI Drawing")
        self.btn_roi_mode.setFixedSize(130, 32)
        self.btn_roi_mode.setCheckable(True)
        self.btn_roi_mode.setChecked(True)
        self.btn_roi_mode.setObjectName("mode-active")
        self.btn_roi_mode.clicked.connect(self._toggle_mode)
        toolbar.addWidget(self.btn_roi_mode)
        mode_group.addButton(self.btn_roi_mode)

        self.btn_manual_mode = QPushButton("✏️ Manual Edit")
        self.btn_manual_mode.setFixedSize(130, 32)
        self.btn_manual_mode.setCheckable(True)
        self.btn_manual_mode.setObjectName("mode-inactive")
        self.btn_manual_mode.clicked.connect(self._toggle_mode)
        toolbar.addWidget(self.btn_manual_mode)
        mode_group.addButton(self.btn_manual_mode)
        
        toolbar.addSeparator()
        
        btn_undo = QPushButton("↩️ Undo Point")
        btn_undo.setFixedSize(120, 32)
        btn_undo.setObjectName("secondary")
        btn_undo.clicked.connect(self._undo_last_point)
        toolbar.addWidget(btn_undo)
        
        btn_clear_all = QPushButton("🗑️ Clear All")
        btn_clear_all.setFixedSize(120, 32)
        btn_clear_all.setObjectName("danger")
        btn_clear_all.clicked.connect(self._clear_polygons)
        toolbar.addWidget(btn_clear_all)
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer)
        
        self.btn_count = QPushButton("▶️ Start Counting")
        self.btn_count.setFixedSize(150, 36)
        self.btn_count.setEnabled(False)
        self.btn_count.clicked.connect(self._start_counting)
        toolbar.addWidget(self.btn_count)

    def _on_region_changed(self, index):
        """Automatically update Vol/Sq based on Chamber and Region"""
        chamber = self.combo_chamber.currentText()
        region = self.combo_region.currentText()
        
        # Standard 0.1mm depth chambers
        if any(x in chamber for x in ["Neubauer", "Watson", "Burker", "Thoma"]):
            if any(x in region for x in ["4 Corners", "1 Center", "Full Plate", "16 Large"]):
                self.spin_volume.setValue(0.0001)
            elif "5 Medium Squares" in region:
                self.spin_volume.setValue(0.000004)
                
        # 0.2mm depth chambers
        elif "Fuchs-Rosenthal" in chamber:
            if "Large Square" in region:
                self.spin_volume.setValue(0.0002)
        
        elif "Custom" in chamber:
            pass # Keep user defined value

    def _on_chamber_changed(self, index):
        """Update region options when chamber type changes"""
        self._update_region_options()

    def _update_region_options(self):
        """Refresh the counting region dropdown based on chamber layout"""
        self.combo_region.blockSignals(True)
        self.combo_region.clear()
        chamber = self.combo_chamber.currentText()
        
        if any(x in chamber for x in ["Neubauer", "Watson", "Burker"]):
            self.combo_region.addItems([
                "4 Corners (Animal Cells)", 
                "1 Center Square (Big)", 
                "5 Medium Squares (Small Cells)", 
                "Full Plate (25 Squares)"
            ])
        elif "Fuchs-Rosenthal" in chamber:
            self.combo_region.addItems([
                "16 Large Squares (Total)",
                "1 Large Square",
                "4 Large Squares"
            ])
        elif "Thoma" in chamber:
            self.combo_region.addItems([
                "1 Center Square (25 Medium)",
                "5 Medium Squares"
            ])
        else:
            self.combo_region.addItems(["Custom Configuration"])
            
        self.combo_region.blockSignals(False)
        self._on_region_changed(0)

    def _toggle_mode(self):
        """Toggle between ROI Drawing and Manual Edit modes"""
        is_manual = self.btn_manual_mode.isChecked() if self.btn_manual_mode else False
        
        # If triggered by a button click, update the other button
        sender = self.sender()
        if sender == self.btn_roi_mode:
            is_manual = False
            self.btn_manual_mode.setChecked(False)
            self.btn_roi_mode.setChecked(True)
        elif sender == self.btn_manual_mode:
            is_manual = True
            self.btn_roi_mode.setChecked(False)
            self.btn_manual_mode.setChecked(True)

        # Update visual style
        if self.btn_roi_mode and self.btn_manual_mode:
            self.btn_roi_mode.setObjectName("mode-active" if not is_manual else "mode-inactive")
            self.btn_manual_mode.setObjectName("mode-active" if is_manual else "mode-inactive")
            self.btn_roi_mode.setStyle(self.btn_roi_mode.style())
            self.btn_manual_mode.setStyle(self.btn_manual_mode.style())

        for viewer in self.viewers:
            viewer.set_mode(PolygonViewer.MODE_MANUAL if is_manual else PolygonViewer.MODE_ROI)
        self._update_status_bar()
    
    def _setup_statusbar(self):
        self.statusBar().showMessage("Ready. Shift+Left to draw ROI.")
        self.status_images = QLabel("📷 Images: 0/4")
        self.statusBar().addPermanentWidget(self.status_images)
        self.status_polygons = QLabel("🔷 ROI: 0/4")
        self.statusBar().addPermanentWidget(self.status_polygons)
    
    def _setup_menu(self):
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        
        file_menu = menubar.addMenu("📁 File")
        file_menu.addAction(QAction("📥 Import Images", self, shortcut=QKeySequence("Ctrl+O"), triggered=self._import_images))
        file_menu.addAction(QAction("💾 Save Results", self, shortcut=QKeySequence("Ctrl+S"), triggered=self._save_results))
        file_menu.addSeparator()
        file_menu.addAction(QAction("🚪 Exit", self, shortcut=QKeySequence("Ctrl+Q"), triggered=self.close))
        
        edit_menu = menubar.addMenu("✏️ Edit")
        edit_menu.addAction(QAction("↩️ Undo Point", self, shortcut=QKeySequence("Ctrl+Z"), triggered=self._undo_last_point))
        edit_menu.addAction(QAction("🗑️ Clear Polygons", self, triggered=self._clear_polygons))
        
        help_menu = menubar.addMenu("❓ Help")
        help_menu.addAction(QAction("ℹ️ About", self, triggered=self._show_about))
    
    def _show_about(self):
        help_text = """
        <div style='color: #ffffff; background-color: #0f0f1a; font-family: "Segoe UI", sans-serif; min-width: 500px; padding: 10px;'>
            <h2 style='color: #00d4ff; text-align: center; border-bottom: 2px solid #00d4ff; padding-bottom: 10px;'>
                🔬 CellCounter v2.1 - User Manual / 操作手册
            </h2>
            
            <div style='margin-top: 15px;'>
                <h3 style='color: #00ff88;'>Step 1: Import / 第一步：导入图片</h3>
                <p>Click <b>"Import Images"</b> to select up to 4 images or a folder.</p>
                <p>点击 <b>"Import Images"</b> 选择最多4张图片或整个文件夹。</p>
            </div>

            <div style='margin-top: 15px;'>
                <h3 style='color: #00ff88;'>Step 2: Define ROI / 第二步：划定计数区域</h3>
                <p>Use <b>Shift + Left Click</b> to draw. Right-click to close.</p>
                <p>使用 <b>Shift + 左键</b> 绘制区域。右键点击闭合。</p>
            </div>

            <div style='margin-top: 15px;'>
                    <h3 style='color: #00ff88;'>Step 3: Auto Count / 第三步：自动计数</h3>
                    <p>Adjust parameters and click <b>"Start All Tabs"</b> to process all images.</p>
                    <p>调整参数并点击 <b>"Start All Tabs"</b> 处理所有图片。</p>
                </div>

            <div style='margin-top: 15px;'>
                <h3 style='color: #00ff88;'>Step 4: Manual Edit / 第四步：手动修正</h3>
                <p>Press <b>'M'</b> for Manual Mode. <b>Left-click</b> add, <b>Right-click</b> remove.</p>
                <p>按 <b>'M'</b> 进入手动模式。<b>左键</b> 添加，<b>右键</b> 删除。</p>
            </div>

            <div style='margin-top: 15px; background-color: #1a1a2e; padding: 10px; border-radius: 5px; border: 1px solid #2a2a4a;'>
                <h3 style='color: #ffcc00; margin-top: 0;'>Shortcuts / 快捷键</h3>
                <table style='width: 100%; color: #ffffff;'>
                    <tr><td><b>1, 2, 3, 4</b></td><td>Switch Tabs / 切换页签</td></tr>
                    <tr><td><b>M</b></td><td>Toggle Mode / 切换模式</td></tr>
                    <tr><td><b>Delete</b></td><td>Clear ROI / 清除区域</td></tr>
                    <tr><td><b>Arrows</b></td><td>Pan / 移动</td></tr>
                    <tr><td><b>+ / -</b></td><td>Zoom / 缩放</td></tr>
                </table>
            </div>
        </div>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("Help & About")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        # Force dark theme style for the message box to avoid white background
        msg.setStyleSheet("""
            QMessageBox { background-color: #0f0f1a; border: 1px solid #2a2a4a; }
            QLabel { color: #ffffff; background-color: transparent; }
            QPushButton { 
                background-color: #2a2a4a; 
                color: white; 
                border-radius: 4px; 
                padding: 5px 15px;
                min-width: 60px;
            }
            QPushButton:hover { background-color: #3a3a6a; }
        """)
        msg.exec()
    
    def _setup_ui(self):
        # Temporarily block signals to prevent triggering save/preview during load
        self.blockSignals(True)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(5)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Scrollable Param Panel
        param_scroll = QScrollArea()
        param_scroll.setWidgetResizable(True)
        param_scroll.setFrameShape(QFrame.Shape.NoFrame)
        param_scroll.setWidget(self._create_param_panel())
        param_scroll.setMinimumWidth(260)
        param_scroll.setMaximumWidth(400)
        
        # Right: Scrollable Result Panel
        result_scroll = QScrollArea()
        result_scroll.setWidgetResizable(True)
        result_scroll.setFrameShape(QFrame.Shape.NoFrame)
        result_scroll.setWidget(self._create_result_panel())
        result_scroll.setMinimumWidth(220)
        result_scroll.setMaximumWidth(350)
        
        splitter.addWidget(param_scroll)
        splitter.addWidget(self._create_image_panel())
        splitter.addWidget(result_scroll)
        
        # Distribute space: Left 20%, Middle 60%, Right 20%
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 6)
        splitter.setStretchFactor(2, 2)
        
        main_layout.addWidget(splitter)
        self.blockSignals(False)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
    
    def _create_param_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        card = QFrame()
        card.setObjectName("cardPanel")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 20, 15, 15)
        card_layout.setSpacing(15)
        
        # Detection Settings
        card_layout.addWidget(QLabel("🔍 Detection Settings", styleSheet="color: #00d4ff; font-weight: bold;"))
        detect_grid = QGridLayout()
        self.spin_min_area = self._add_spinbox(detect_grid, "Min Area:", 0, 1, 20, 1, 10000)
        self.spin_max_area = self._add_spinbox(detect_grid, "Max Area:", 1, 1, 1000, 10, 100000)
        
        detect_grid.addWidget(QLabel("Circularity:"), 2, 0)
        self.chk_circularity = QComboBox()
        self.chk_circularity.addItems(["Enabled", "Disabled"])
        detect_grid.addWidget(self.chk_circularity, 2, 1)
        
        self.spin_circularity = self._add_spinbox(detect_grid, "Min Circ:", 3, 1, 40, 1, 100, "%")
        
        # Connect detection signals
        self.spin_min_area.valueChanged.connect(self._on_param_changed)
        self.spin_max_area.valueChanged.connect(self._on_param_changed)
        self.chk_circularity.currentIndexChanged.connect(self._on_param_changed)
        self.spin_circularity.valueChanged.connect(self._on_param_changed)
        
        card_layout.addLayout(detect_grid)
        card_layout.addWidget(self._create_separator())
        
        # Algorithm & Calc
        card_layout.addWidget(QLabel("🧪 Algorithm & Calc", styleSheet="color: #00d4ff; font-weight: bold;"))
        calc_grid = QGridLayout()

        self.combo_chamber = QComboBox()
        self.combo_chamber.addItems([
            "Improved Neubauer (Standard)",
            "Watson (Disposable)",
            "Fuchs-Rosenthal (CSF)",
            "Burker-Turk",
            "Thoma",
            "Custom"
        ])
        self.combo_chamber.currentIndexChanged.connect(self._on_chamber_changed)
        self.combo_chamber.currentIndexChanged.connect(self._on_param_changed)
        calc_grid.addWidget(QLabel("Chamber Type:"), 0, 0); calc_grid.addWidget(self.combo_chamber, 0, 1)

        self.spin_dilution = QDoubleSpinBox()
        self.spin_dilution.setRange(1.0, 10000.0); self.spin_dilution.setValue(1.0); self.spin_dilution.setSingleStep(0.1)
        self.spin_dilution.valueChanged.connect(self._on_param_changed)
        calc_grid.addWidget(QLabel("Dilution Factor:"), 1, 0); calc_grid.addWidget(self.spin_dilution, 1, 1)

        self.combo_region = QComboBox()
        self.combo_region.currentIndexChanged.connect(self._on_region_changed)
        self.combo_region.currentIndexChanged.connect(self._on_param_changed)
        calc_grid.addWidget(QLabel("Counting Region:"), 2, 0); calc_grid.addWidget(self.combo_region, 2, 1)

        self.spin_volume = QDoubleSpinBox()
        self.spin_volume.setDecimals(8); self.spin_volume.setRange(0.0, 1.0); self.spin_volume.setValue(0.0001)
        self.spin_volume.setSingleStep(0.00001)
        self.spin_volume.valueChanged.connect(self._on_param_changed)
        calc_grid.addWidget(QLabel("Vol/Sq (mL):"), 3, 0); calc_grid.addWidget(self.spin_volume, 3, 1)

        self._update_region_options() # Initial populate now that all widgets are ready
        
        card_layout.addLayout(calc_grid)
        
        card_layout.addStretch()
        self.btn_count_main = QPushButton("🚀 Start All Tabs", objectName="primary")
        self.btn_count_main.clicked.connect(self._start_counting)
        card_layout.addWidget(self.btn_count_main)
        
        layout.addWidget(card)
        return panel

    def _on_param_changed(self):
        """Handle parameter changes: save settings and update UI without re-detecting"""
        self._save_settings()
        self._update_table_results()
        self._update_status_bar()

    def _update_current_preview(self):
        """Run detection only for the currently active tab for real-time feedback"""
        idx = self.image_tabs.currentIndex()
        path = self.image_paths[idx]
        if not path: return
        
        viewer = self.viewers[idx]
        mask = viewer.get_polygon_mask() # Assume get_polygon_mask is updated to not require shape
        if mask is None: return
        
        img = cv2_imread(path)
        if img is None: return
        
        # Get current params
        min_area = self.spin_min_area.value()
        max_area = self.spin_max_area.value()
        use_circ = self.chk_circularity.currentText() == "Enabled"
        min_circ = self.spin_circularity.value() / 100.0
        
        # Detect
        cells = detect_cells_in_roi(img, mask, min_area, max_area, use_circ, min_circ)
        viewer.set_preview_cells(cells)
        
        # Update table for this image
        self.cell_counts[idx] = len(cells)
        self._update_table_results()

    def _add_spinbox(self, layout, label, row, col, val, step, max_val, suffix=""):
        layout.addWidget(QLabel(label), row, 0)
        spin = QSpinBox()
        spin.setRange(0, max_val); spin.setValue(val); spin.setSingleStep(step); spin.setSuffix(suffix)
        layout.addWidget(spin, row, col)
        return spin

    def _create_result_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        card = QFrame(objectName="cardPanel")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 20, 15, 15)
        
        header_label = QLabel("📊 Statistics & Results")
        header_label.setStyleSheet("color: #00d4ff; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        card_layout.addWidget(header_label)

        self.result_table = QTableWidget(5, 2)
        self.result_table.setHorizontalHeaderLabels(["Image Source", "Cell Count"])
        self.result_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setShowGrid(False)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setStyleSheet("""
            QTableWidget { background-color: #1a1a2e; border: none; }
            QTableWidget::item { border-bottom: 1px solid #2a2a4a; padding: 10px; }
        """)
        
        for i, name in enumerate(["📷 Image 1", "📷 Image 2", "📷 Image 3", "📷 Image 4", "📈 TOTAL"]):
            item_name = QTableWidgetItem(name)
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if i == 4:
                item_name.setForeground(Qt.GlobalColor.cyan)
                font = item_name.font()
                font.setBold(True)
                item_name.setFont(font)
            self.result_table.setItem(i, 0, item_name)
            
            item_val = QTableWidgetItem("0")
            item_val.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if i == 4: # Total is not editable
                item_val.setFlags(item_val.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item_val.setForeground(Qt.GlobalColor.cyan)
                font = item_val.font()
                font.setBold(True)
                item_val.setFont(font)
            self.result_table.setItem(i, 1, item_val)
        
        self.result_table.itemChanged.connect(self._on_table_item_changed)
        card_layout.addWidget(self.result_table)

        # Sample Volume input moved here
        vol_input_layout = QHBoxLayout()
        vol_input_layout.addWidget(QLabel("Sample Vol (mL):", styleSheet="color: #888;"))
        self.spin_total_vol = QDoubleSpinBox()
        self.spin_total_vol.setRange(0.0, 1000000.0); self.spin_total_vol.setValue(1.0)
        self.spin_total_vol.setSingleStep(1.0); self.spin_total_vol.setSuffix(" mL")
        self.spin_total_vol.valueChanged.connect(self._on_param_changed)
        vol_input_layout.addWidget(self.spin_total_vol)
        card_layout.addLayout(vol_input_layout)
        
        conc_card = QFrame(styleSheet="background-color: #1a1a2e; border-radius: 10px; border: 1px solid #2a2a4a;")
        conc_layout = QVBoxLayout(conc_card)
        self.conc_label = QLabel("--", alignment=Qt.AlignmentFlag.AlignCenter, styleSheet="font-size: 32px; font-weight: bold; color: #00d4ff; border: none;")
        conc_layout.addWidget(self.conc_label)
        conc_layout.addWidget(QLabel("cells/mL", alignment=Qt.AlignmentFlag.AlignCenter, styleSheet="color: #888; font-size: 12px; border: none;"))
        card_layout.addWidget(conc_card)

        total_sample_card = QFrame(styleSheet="background-color: #1a1a2e; border-radius: 10px; border: 1px solid #2a2a4a; margin-top: 5px;")
        total_sample_layout = QVBoxLayout(total_sample_card)
        self.total_sample_label = QLabel("--", alignment=Qt.AlignmentFlag.AlignCenter, styleSheet="font-size: 24px; font-weight: bold; color: #00ff88; border: none;")
        total_sample_layout.addWidget(self.total_sample_label)
        total_sample_layout.addWidget(QLabel("total cells in sample", alignment=Qt.AlignmentFlag.AlignCenter, styleSheet="color: #888; font-size: 11px; border: none;"))
        card_layout.addWidget(total_sample_card)
        
        card_layout.addStretch()
        self.btn_save_report = QPushButton("💾 Export Report", objectName="primary", enabled=False)
        self.btn_save_report.clicked.connect(self._save_results)
        card_layout.addWidget(self.btn_save_report)
        
        layout.addWidget(card)
        return panel

    def _create_image_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel); layout.setContentsMargins(0, 0, 0, 0)
        self.image_tabs = QTabWidget()
        self.image_tabs.currentChanged.connect(self._update_status_bar)
        self.viewers: List[PolygonViewer] = []
        for i in range(4):
            tab = QWidget(); tab_layout = QVBoxLayout(tab)
            viewer = PolygonViewer()
            viewer.polygon_changed.connect(lambda idx=i: self._on_polygon_changed(idx))
            self.viewers.append(viewer)
            tab_layout.addWidget(viewer)
            self.image_tabs.addTab(tab, f"📷 Image {i+1}")
        layout.addWidget(self.image_tabs)
        return panel

    def _create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine); line.setFrameShadow(QFrame.Shadow.Plain)
        line.setStyleSheet("background-color: #2a2a4a; max-height: 1px;")
        return line

    def _import_images(self):
        # Support both individual files and folders
        msg = QMessageBox()
        msg.setWindowTitle("Import Images")
        msg.setText("Choose import method:")
        btn_files = msg.addButton("Select Files", QMessageBox.ButtonRole.ActionRole)
        btn_folder = msg.addButton("Select Folder", QMessageBox.ButtonRole.ActionRole)
        msg.addButton(QMessageBox.StandardButton.Cancel)
        msg.exec()

        files = []
        if msg.clickedButton() == btn_files:
            files, _ = QFileDialog.getOpenFileNames(
                self, "Select Images", self.last_dir, 
                "Images (*.jpg *.jpeg *.png *.bmp *.webp *.tiff *.tif);;All Files (*)"
            )
            if files:
                self.last_dir = os.path.dirname(files[0])
                self._save_settings()
        elif msg.clickedButton() == btn_folder:
            folder = QFileDialog.getExistingDirectory(self, "Select Folder", self.last_dir)
            if folder:
                self.last_dir = folder
                self._save_settings()
                # Get first 4 valid images from folder
                valid_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif')
                files = [os.path.join(folder, f) for f in os.listdir(folder) 
                        if f.lower().endswith(valid_exts)]
                print(f"DEBUG: Found {len(files)} valid images in {folder}")
                if files:
                    print(f"DEBUG: First few files: {files[:3]}")
        
        if not files: return
        
        # Apply natural sorting to ensure order matches user expectation (1, 2, 10...)
        files.sort(key=natural_sort_key)
        
        current_idx = self.image_tabs.currentIndex()
        for i, path in enumerate(files):
            target_idx = (current_idx + i) % 4
            self.image_paths[target_idx] = path
            self.viewers[target_idx].load_image(path)
            
        self._update_ui_state()
        self._update_status_bar()
        self._update_table_results()

    def _on_image_dropped(self, viewer, path):
        idx = self.viewers.index(viewer)
        self.image_paths[idx] = path
        self._update_ui_state()
        self._update_status_bar()
        self._update_table_results()

    def _on_polygon_changed(self, idx: int):
        self._update_ui_state()
        self._update_status_bar()
        
        viewer = self.viewers[idx]
        if viewer.current_mode == PolygonViewer.MODE_MANUAL:
            # In manual mode, update count from viewer's existing preview_cells
            self.cell_counts[idx] = len(viewer.preview_cells)
            self._update_table_results()
        else:
            # In ROI mode, do NOT trigger auto-detection anymore as per user request
            self._update_table_results()

    def _on_table_item_changed(self, item):
        """Handle manual edits in the results table"""
        if item.column() != 1 or item.row() == 4: # Only handle Count column, skip Total
            return
            
        try:
            new_val = int(item.text())
            if new_val < 0: raise ValueError
            
            # Temporarily block signals to avoid infinite loop
            self.result_table.blockSignals(True)
            
            # Update internal count
            self.cell_counts[item.row()] = new_val
            
            # Recalculate total and concentration
            total_cells = sum(self.cell_counts)
            
            # Update Total row in table
            total_item = self.result_table.item(4, 1)
            if total_item:
                total_item.setText(str(total_cells))
            
            # Update Concentration label
            import re
            text = self.combo_region.currentText()
            match = re.search(r'(\d+)', text)
            num_sq = int(match.group(1)) if match else 1
            conc = calculate_concentration(total_cells, self.spin_dilution.value(), num_sq, self.spin_volume.value())
            self.conc_label.setText(f"{conc:.2e}")

            # Update Total Sample Label
            total_sample = conc * self.spin_total_vol.value()
            self.total_sample_label.setText(f"{total_sample:.2e}")
            
            self.result_table.blockSignals(False)
            
        except ValueError:
            # Revert to old value if input is invalid
            self.result_table.blockSignals(True)
            item.setText(str(self.cell_counts[item.row()]))
            self.result_table.blockSignals(False)

    def _update_table_results(self):
        if self.result_table is None or self.conc_label is None or self.total_sample_label is None:
            return
        """Sync cell counts and concentration to the table in real-time"""
        self.result_table.blockSignals(True) # Don't trigger _on_table_item_changed
        total_cells = 0
        for i, viewer in enumerate(self.viewers):
            # Combined count: auto-detected cells + manual edits
            count = len(viewer.preview_cells)
            self.cell_counts[i] = count
            total_cells += count
            
            item = self.result_table.item(i, 1)
            if item:
                item.setText(str(count))
        
        # Calculate concentration
        import re
        text = self.combo_region.currentText()
        match = re.search(r'(\d+)', text)
        num_sq = int(match.group(1)) if match else 1
        
        conc = calculate_concentration(total_cells, self.spin_dilution.value(), num_sq, self.spin_volume.value())
        self.conc_label.setText(f"{conc:.2e}")
        
        total_item = self.result_table.item(4, 1)
        if total_item:
            total_item.setText(str(total_cells))
            
        # Update Total Sample Label
        total_sample = conc * self.spin_total_vol.value()
        self.total_sample_label.setText(f"{total_sample:.2e}")
            
        self.result_table.blockSignals(False)

    def _undo_last_point(self):
        viewer = self.viewers[self.image_tabs.currentIndex()]
        if viewer.polygon_points: viewer.polygon_points.pop(); viewer.update(); self._on_polygon_changed(self.image_tabs.currentIndex())

    def _clear_polygons(self):
        """Clear ROI and cells for the currently active tab only"""
        current_idx = self.image_tabs.currentIndex()
        self.viewers[current_idx].clear_polygon()
        self._update_status_bar()
        self._update_table_results()

    def _update_status_bar(self):
        if self.status_images is None or self.btn_roi_mode is None or self.btn_manual_mode is None:
            return
            
        img_cnt = sum(1 for p in self.image_paths if p)
        roi_cnt = sum(1 for v in self.viewers if len(v.polygon_points) >= 3)
        self.status_images.setText(f"📷 Images: {img_cnt}/4")
        self.status_polygons.setText(f"🔷 ROI: {roi_cnt}/4")
        
        idx = self.image_tabs.currentIndex()
        path = self.image_paths[idx]
        filename = os.path.basename(path) if path else "No Image"
        
        viewer = self.viewers[idx]
        roi_points = len(viewer.polygon_points)
        cell_count = self.cell_counts[idx]
        
        # Use viewer mode if available, or fallback to UI button state
        is_manual = self.btn_manual_mode.isChecked()
        mode_str = "MANUAL EDIT (Click to +/- cells)" if is_manual else "ROI DRAWING (Shift+Left to add)"
        
        status = f"Tab {idx+1}: {filename} | Mode: {mode_str} | ROI Points: {roi_points} | Cells: {cell_count}"
        self.statusBar().showMessage(status)

    def _update_ui_state(self):
        """
        Enable counting button if there's at least one image with a valid ROI (3+ points).
        """
        has_valid_roi = False
        for i in range(4):
            if self.image_paths[i] and len(self.viewers[i].polygon_points) >= 3:
                has_valid_roi = True
                break
        
        self.btn_count.setEnabled(has_valid_roi)
        self.btn_count_main.setEnabled(has_valid_roi)

    def _start_counting(self):
        total_cells = 0
        self.progress_bar.setVisible(True); self.progress_bar.setValue(0)
        
        # Disable UI during calculation to prevent conflicting operations
        self.setEnabled(False)
        
        try:
            min_area = self.spin_min_area.value()
            max_area = self.spin_max_area.value()
            use_circ = self.chk_circularity.currentText() == "Enabled"
            min_circ = self.spin_circularity.value() / 100.0
            
            for i, path in enumerate(self.image_paths):
                if not path: continue
                
                # Update status message
                self.statusBar().showMessage(f"Processing image {i+1}/4: {os.path.basename(path)}...")
                QtWidgets.QApplication.processEvents()
                
                img = cv2_imread(path)
                if img is None: continue
                
                mask = self.viewers[i].get_polygon_mask(img.shape)
                if mask is not None:
                    # Detect cells
                    cells = detect_cells_in_roi(img, mask, min_area, max_area, use_circ, min_circ)
                    self.cell_counts[i] = len(cells)
                    total_cells += len(cells)
                    self.viewers[i].set_preview_cells(cells)
                
                # Update progress and allow UI to refresh
                self.progress_bar.setValue((i + 1) * 25)
                QtWidgets.QApplication.processEvents()            
                
            self._update_table_results()
            self.btn_save_report.setEnabled(True)
            self.statusBar().showMessage("Counting completed.", 5000)
            
        finally:
            self.progress_bar.setVisible(False)
            self.setEnabled(True)
            # Re-enable UI and focus back
            self.activateWindow()

    def _save_results(self):
        # Implementation simplified for brevity, similar to previous version but using refactored logic
        path = QFileDialog.getSaveFileName(self, "Save Report", os.path.join(self.last_dir, "results.csv"), "CSV Files (*.csv)")[0]
        if path:
            self.last_dir = os.path.dirname(path)
            self._save_settings()
            with open(path, 'w') as f:
                f.write(f"Total Cells,{sum(self.cell_counts)}\nConcentration,{self.conc_label.text()}\n")
            QMessageBox.information(self, "Saved", f"Report saved to {path}")

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = CellCounterGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
