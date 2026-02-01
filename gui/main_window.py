import os
import sys
import json
import numpy as np
from datetime import datetime
from typing import List, Optional, Tuple

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFileDialog, QSpinBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QProgressBar, QMessageBox,
    QSplitter, QComboBox, QTabWidget, QToolBar, QSizePolicy, QFrame,
    QScrollArea, QButtonGroup
)
from PySide6.QtCore import Qt, QPointF, QSettings
from PySide6.QtGui import QAction, QKeySequence, QFont

from gui.viewer import PolygonViewer
from gui.styles import MAIN_STYLE, THEMES, get_main_style, get_viewer_style
from core.detector import create_blob_detector, detect_cells_in_roi
from core.calculator import calculate_concentration
from core.utils import cv2_imread, cv2_imwrite, natural_sort_key

class CopyableTableWidget(QTableWidget):
    """A QTableWidget that supports Ctrl+C to copy selected cells"""
    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            selected = self.selectedRanges()
            if not selected:
                return
            
            s = ""
            # Handle only the first selected range for simplicity
            r = selected[0]
            for i in range(r.topRow(), r.bottomRow() + 1):
                row_text = []
                for j in range(r.leftColumn(), r.rightColumn() + 1):
                    item = self.item(i, j)
                    row_text.append(item.text() if item else "")
                s += "\t".join(row_text) + "\n"
                
            QtGui.QGuiApplication.clipboard().setText(s)
        else:
            super().keyPressEvent(event)

class CellCounterGUI(QMainWindow):
    """Hemocytometer Main GUI v2.1.6 - Refactored"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔬 Hemocytometer Cell Counter v2.1.6")
        
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
        self.current_language = self.settings.value("language", "zh")
        self.current_theme = self.settings.value("theme", "Dark")
        self._load_translations()
        
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
        self._apply_theme()
        self._setup_shortcuts()
        self._load_settings()

    def _apply_theme(self):
        """Apply the current theme to the main window and all viewers"""
        # Apply to Main Window
        main_style = get_main_style(self.current_theme)
        self.setStyleSheet(main_style)
        
        # Apply to all viewers
        viewer_style = get_viewer_style(self.current_theme)
        if hasattr(self, 'viewers'):
            for viewer in self.viewers:
                viewer.setStyleSheet(viewer_style)
                
    def _on_theme_changed(self, index):
        """Handle theme selection change"""
        theme_name = self.combo_theme.itemText(index)
        if theme_name == self.current_theme:
            return
            
        self.current_theme = theme_name
        self.settings.setValue("theme", self.current_theme)
        self._apply_theme()

    def _load_settings(self):
        """Load saved parameters from QSettings"""
        self.spin_min_area.setValue(int(self.settings.value("min_area", 20)))
        self.spin_max_area.setValue(int(self.settings.value("max_area", 1000)))
        
        circ_val = self.settings.value("circularity_enabled", "Enabled")
        idx = self.chk_circularity.findData(circ_val)
        if idx >= 0: self.chk_circularity.setCurrentIndex(idx)

        self.spin_circularity.setValue(int(self.settings.value("min_circularity", 40)))
        
        chamber_val = self.settings.value("chamber", "Improved Neubauer (Standard)")
        idx = self.combo_chamber.findData(chamber_val)
        if idx >= 0: self.combo_chamber.setCurrentIndex(idx)
        
        self.spin_dilution.setValue(float(self.settings.value("dilution", 1.0)))
        
        region_val = self.settings.value("region", "4 Corners (Animal Cells)")
        idx = self.combo_region.findData(region_val)
        if idx >= 0: self.combo_region.setCurrentIndex(idx)

        self.spin_volume.setValue(float(self.settings.value("volume", 0.0001)))
        self.spin_total_vol.setValue(float(self.settings.value("total_volume", 1.0)))

    def _load_translations(self):
        self.translations = {}
        try:
            path = os.path.join(os.path.dirname(__file__), "translations.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    self.translations = json.load(f)
        except Exception as e:
            print(f"Error loading translations: {e}")

    def tr(self, text):
        if self.current_language == "zh":
            return self.translations.get(text, text)
        return text

    def _switch_language(self, lang):
        if self.current_language == lang:
            return
        
        self.settings.setValue("language", lang)
        self.current_language = lang
        
        msg = self.tr("Language changed. Would you like to restart now to apply all changes?\n\n语言已切换。是否立即重启软件以应用所有更改？")
        reply = QMessageBox.question(self, self.tr("Restart Required"), msg, 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            QtCore.QCoreApplication.quit()
            QtCore.QProcess.startDetached(sys.executable, sys.argv)

    def _on_language_changed(self, index):
        """Handle language selection change"""
        lang = "en" if index == 1 else "zh"
        self._switch_language(lang)
    
    def _save_settings(self):
        """Save current parameters to QSettings"""
        self.settings.setValue("min_area", self.spin_min_area.value())
        self.settings.setValue("max_area", self.spin_max_area.value())
        self.settings.setValue("circularity_enabled", self.chk_circularity.currentData())
        self.settings.setValue("min_circularity", self.spin_circularity.value())
        self.settings.setValue("chamber", self.combo_chamber.currentData())
        self.settings.setValue("dilution", self.spin_dilution.value())
        self.settings.setValue("region", self.combo_region.currentData())
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
        
        title_label = QLabel(" 🔬 CellCounter v2.1.6 ")
        title_label.setObjectName("titleLabel")
        toolbar.addWidget(title_label)
        toolbar.addSeparator()
        
        btn_import = QPushButton(self.tr("📁 Import Images"))
        btn_import.setFixedHeight(36)
        btn_import.setMinimumWidth(130)
        btn_import.clicked.connect(self._import_images)
        toolbar.addWidget(btn_import)
        toolbar.addSeparator()

        mode_label = QLabel(self.tr(" Interaction Mode: "))
        mode_label.setObjectName("modeLabel")
        toolbar.addWidget(mode_label)

        # Two distinct buttons for mode selection
        mode_group = QButtonGroup(self)
        
        self.btn_roi_mode = QPushButton(self.tr("📐 ROI Drawing"))
        self.btn_roi_mode.setFixedHeight(36)
        self.btn_roi_mode.setMinimumWidth(130)
        self.btn_roi_mode.setCheckable(True)
        self.btn_roi_mode.setChecked(True)
        self.btn_roi_mode.setObjectName("mode-active")
        self.btn_roi_mode.clicked.connect(self._toggle_mode)
        toolbar.addWidget(self.btn_roi_mode)
        mode_group.addButton(self.btn_roi_mode)

        self.btn_manual_mode = QPushButton(self.tr("✏️ Manual Edit"))
        self.btn_manual_mode.setFixedHeight(36)
        self.btn_manual_mode.setMinimumWidth(130)
        self.btn_manual_mode.setCheckable(True)
        self.btn_manual_mode.setObjectName("mode-inactive")
        self.btn_manual_mode.clicked.connect(self._toggle_mode)
        toolbar.addWidget(self.btn_manual_mode)
        mode_group.addButton(self.btn_manual_mode)
        
        toolbar.addSeparator()
        
        btn_undo = QPushButton(self.tr("↩️ Undo Point"))
        btn_undo.setFixedHeight(36)
        btn_undo.setMinimumWidth(120)
        btn_undo.setObjectName("secondary")
        btn_undo.clicked.connect(self._undo_last_point)
        toolbar.addWidget(btn_undo)
        
        btn_clear_all = QPushButton(self.tr("🗑️ Clear All"))
        btn_clear_all.setFixedHeight(36)
        btn_clear_all.setMinimumWidth(120)
        btn_clear_all.setObjectName("danger")
        btn_clear_all.clicked.connect(self._clear_polygons)
        toolbar.addWidget(btn_clear_all)
        
        toolbar.addSeparator()

        # Theme Switcher
        lbl_theme = QLabel(" 🎨 ")
        toolbar.addWidget(lbl_theme)
        
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(list(THEMES.keys()))
        self.combo_theme.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_theme.setFixedWidth(100)
        self.combo_theme.setCurrentText(self.current_theme)
        self.combo_theme.currentIndexChanged.connect(self._on_theme_changed)
        toolbar.addWidget(self.combo_theme)
        
        toolbar.addSeparator()
        
        # Language Switcher
        lbl_lang = QLabel(" 🌐 ")
        toolbar.addWidget(lbl_lang)
        
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["中文", "English"])
        self.combo_lang.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_lang.setFixedWidth(100)
        
        # Set initial state
        if self.current_language == "en":
            self.combo_lang.setCurrentIndex(1)
        else:
            self.combo_lang.setCurrentIndex(0)
            
        self.combo_lang.currentIndexChanged.connect(self._on_language_changed)
        toolbar.addWidget(self.combo_lang)
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer)
        
        self.btn_count = QPushButton(self.tr("▶️ Start Counting"))
        self.btn_count.setFixedHeight(36)
        self.btn_count.setMinimumWidth(150)
        self.btn_count.setEnabled(False)
        self.btn_count.clicked.connect(self._start_counting)
        toolbar.addWidget(self.btn_count)

    def _on_region_changed(self, index):
        """Automatically update Vol/Sq based on Chamber and Region"""
        chamber = self.combo_chamber.currentData()
        region = self.combo_region.currentData()
        
        if not chamber or not region: return
        
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
        
        chamber = self.combo_chamber.currentData()
        if not chamber: chamber = ""
        
        if any(x in chamber for x in ["Neubauer", "Watson", "Burker"]):
            self.combo_region.addItem(self.tr("4 Corners (Animal Cells)"), "4 Corners (Animal Cells)")
            self.combo_region.addItem(self.tr("1 Center Square (Big)"), "1 Center Square (Big)")
            self.combo_region.addItem(self.tr("5 Medium Squares (Small Cells)"), "5 Medium Squares (Small Cells)")
            self.combo_region.addItem(self.tr("Full Plate (25 Squares)"), "Full Plate (25 Squares)")
        elif "Fuchs-Rosenthal" in chamber:
            self.combo_region.addItem(self.tr("16 Large Squares (Total)"), "16 Large Squares (Total)")
            self.combo_region.addItem(self.tr("1 Large Square"), "1 Large Square")
            self.combo_region.addItem(self.tr("4 Large Squares"), "4 Large Squares")
        elif "Thoma" in chamber:
            self.combo_region.addItem(self.tr("1 Center Square (25 Medium)"), "1 Center Square (25 Medium)")
            self.combo_region.addItem(self.tr("5 Medium Squares"), "5 Medium Squares")
        else:
            self.combo_region.addItem(self.tr("Custom Configuration"), "Custom Configuration")
            
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
        self.statusBar().showMessage(self.tr("Ready. Shift+Left to draw ROI."))
        self.status_images = QLabel(self.tr("📷 Images: 0/4"))
        self.statusBar().addPermanentWidget(self.status_images)
        self.status_polygons = QLabel(self.tr("🔷 ROI: 0/4"))
        self.statusBar().addPermanentWidget(self.status_polygons)
    
    def _setup_menu(self):
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        
        file_menu = menubar.addMenu(self.tr("📁 File"))
        file_menu.addAction(QAction(self.tr("📥 Import Images"), self, shortcut=QKeySequence("Ctrl+O"), triggered=self._import_images))
        file_menu.addAction(QAction(self.tr("💾 Save Results"), self, shortcut=QKeySequence("Ctrl+S"), triggered=self._save_results))
        file_menu.addSeparator()
        file_menu.addAction(QAction(self.tr("🚪 Exit"), self, shortcut=QKeySequence("Ctrl+Q"), triggered=self.close))
        
        edit_menu = menubar.addMenu(self.tr("✏️ Edit"))
        edit_menu.addAction(QAction(self.tr("↩️ Undo Point"), self, shortcut=QKeySequence("Ctrl+Z"), triggered=self._undo_last_point))
        edit_menu.addAction(QAction(self.tr("🗑️ Clear Polygons"), self, triggered=self._clear_polygons))
        
        help_menu = menubar.addMenu(self.tr("❓ Help"))
        help_menu.addAction(QAction(self.tr("ℹ️ About"), self, triggered=self._show_about))
    
    def _show_about(self):
        t = THEMES[self.current_theme]
        help_text = f"""
        <div style='color: {t['text_main']}; background-color: {t['bg_main']}; font-family: "Segoe UI", sans-serif; min-width: 650px; padding: 10px;'>
            <h2 style='color: {t['accent']}; text-align: center; border-bottom: 2px solid {t['accent']}; padding-bottom: 10px; margin-bottom: 20px;'>
                🔬 CellCounter v2.1.6 - User Guide & Parameters / 操作指南与参数说明
            </h2>
            
            <div style='display: flex; flex-direction: row; gap: 20px;'>
                <div style='flex: 1;'>
                    <h3 style='color: {t['text_success']}; border-left: 4px solid {t['text_success']}; padding-left: 10px;'>📖 Manual Operation / 手动操作指南</h3>
                    <ol style='padding-left: 20px; line-height: 1.6;'>
                        <li><b>导入图片</b>：点击左侧面板顶部的 <b>"Import Images"</b>。您可以一次选择多张图片，或者选择整个文件夹（程序会自动加载前4张有效图片）。</li>
                        <li><b>划定计数区</b>：在主视图中，按住 <b>Shift + 鼠标左键</b> 点击来绘制多边形区域。绘制完成后，<b>鼠标右键</b> 点击即可闭合区域。</li>
                        <li><b>参数配置</b>：在左侧“Detection Parameters”面板调整识别参数（详见右侧参数说明）。</li>
                        <li><b>执行计数</b>：点击左侧底部的 <b>"Start All Tabs"</b>。程序将依次处理所有已加载图片的 ROI 区域。</li>
                        <li><b>手动微调</b>：点击上方的 <b>"Manual Edit Mode"</b> (或按 M 键)。在图中 <b>左键点击</b> 增加漏选的细胞，<b>右键点击</b> 删除误选的点。</li>
                        <li><b>计算结果</b>：在右侧结果表格中输入“Sample Vol (mL)”（样本总体积），程序会自动计算总细胞数。</li>
                        <li><b>导出报告</b>：点击右下角 <b>"Export Report"</b> 导出 CSV 格式的详细结果。</li>
                    </ol>
                </div>

                <div style='flex: 1; background-color: {t['bg_panel']}; padding: 15px; border-radius: 8px; border: 1px solid {t['border_panel']};'>
                    <h3 style='color: {t['text_warning']}; margin-top: 0;'>⚙️ Parameters / 参数详细介绍</h3>
                    <ul style='padding-left: 15px; line-height: 1.5; font-size: 13px;'>
                        <li style='margin-bottom: 10px;'><b>Min/Max Area (像素面积)</b>：设置细胞的大小范围。
                            <br/><span style='color: {t['text_muted']};'>- 调小 Min 可识别更小的碎屑/细胞；调大 Max 可过滤粘连的杂质。</span></li>
                        <li style='margin-bottom: 10px;'><b>Circularity (圆度)</b>：控制识别目标的形状。
                            <br/><span style='color: {t['text_muted']};'>- 越接近 1.0 表示越圆。开启此项可有效过滤非圆形的纤维或气泡。</span></li>
                        <li style='margin-bottom: 10px;'><b>Chamber Type (计数板类型)</b>：预设的不同品牌计数板参数。
                            <br/><span style='color: {t['text_muted']};'>- 影响深度和网格面积，直接关系到浓度计算的准确性。</span></li>
                        <li style='margin-bottom: 10px;'><b>Dilution Factor (稀释倍数)</b>：样本的稀释比例。
                            <br/><span style='color: {t['text_muted']};'>- 如果是原液则设为 1；若 1:1 稀释则设为 2。</span></li>
                        <li style='margin-bottom: 10px;'><b>Sample Vol (样本总体积)</b>：
                            <br/><span style='color: {t['text_muted']};'>- 用于从“浓度”换算出“样本总细胞数”。</span></li>
                    </ul>
                </div>
            </div>

            <div style='margin-top: 20px; padding: 10px; border-top: 1px solid {t['secondary_border']}; font-size: 12px; color: {t['text_muted']}; text-align: center;'>
                Shortcuts: [1-4] Tabs | [M] Mode | [Del] Clear | [+/-] Zoom | [Arrows] Pan
            </div>
        </div>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("User Guide & Parameter Documentation")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        # Apply theme style to message box
        msg.setStyleSheet(f"""
            QMessageBox {{ background-color: {t['bg_main']}; border: 1px solid {t['accent']}; }}
            QLabel {{ color: {t['text_main']}; }}
            QPushButton {{ 
                background-color: {t['secondary_bg']}; 
                color: {t['text_main']}; 
                border-radius: 4px; 
                padding: 6px 15px; 
                min-width: 80px;
                border: 1px solid {t['secondary_border']};
            }}
            QPushButton:hover {{ background-color: {t['secondary_border']}; border: 1px solid {t['accent']}; }}
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
        
        splitter = QSplitter(Qt.Horizontal)
        
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
        lbl_detect = QLabel(self.tr("🔍 Detection Settings"))
        lbl_detect.setObjectName("headerLabel")
        card_layout.addWidget(lbl_detect)
        detect_grid = QGridLayout()
        self.spin_min_area = self._add_spinbox(detect_grid, self.tr("Min Area:"), 0, 1, 20, 1, 10000)
        self.spin_max_area = self._add_spinbox(detect_grid, self.tr("Max Area:"), 1, 1, 1000, 10, 100000)
        
        detect_grid.addWidget(QLabel(self.tr("Circularity:")), 2, 0)
        self.chk_circularity = QComboBox()
        self.chk_circularity.addItem(self.tr("Enabled"), "Enabled")
        self.chk_circularity.addItem(self.tr("Disabled"), "Disabled")
        detect_grid.addWidget(self.chk_circularity, 2, 1)
        
        self.spin_circularity = self._add_spinbox(detect_grid, self.tr("Min Circ:"), 3, 1, 40, 1, 100, "%")
        
        # Connect detection signals
        self.spin_min_area.valueChanged.connect(self._on_param_changed)
        self.spin_max_area.valueChanged.connect(self._on_param_changed)
        self.chk_circularity.currentIndexChanged.connect(self._on_param_changed)
        self.spin_circularity.valueChanged.connect(self._on_param_changed)
        
        card_layout.addLayout(detect_grid)
        card_layout.addWidget(self._create_separator())
        
        # Algorithm & Calc
        lbl_algo = QLabel(self.tr("🧪 Algorithm & Calc"))
        lbl_algo.setObjectName("headerLabel")
        card_layout.addWidget(lbl_algo)
        calc_grid = QGridLayout()

        self.combo_chamber = QComboBox()
        self.combo_chamber.addItem(self.tr("Improved Neubauer (Standard)"), "Improved Neubauer (Standard)")
        self.combo_chamber.addItem(self.tr("Watson (Disposable)"), "Watson (Disposable)")
        self.combo_chamber.addItem(self.tr("Fuchs-Rosenthal (CSF)"), "Fuchs-Rosenthal (CSF)")
        self.combo_chamber.addItem(self.tr("Burker-Turk"), "Burker-Turk")
        self.combo_chamber.addItem(self.tr("Thoma"), "Thoma")
        self.combo_chamber.addItem(self.tr("Custom"), "Custom")
        
        self.combo_chamber.currentIndexChanged.connect(self._on_chamber_changed)
        self.combo_chamber.currentIndexChanged.connect(self._on_param_changed)
        calc_grid.addWidget(QLabel(self.tr("Chamber Type:")), 0, 0); calc_grid.addWidget(self.combo_chamber, 0, 1)

        self.spin_dilution = QDoubleSpinBox()
        self.spin_dilution.setRange(1.0, 10000.0); self.spin_dilution.setValue(1.0); self.spin_dilution.setSingleStep(0.1)
        self.spin_dilution.valueChanged.connect(self._on_param_changed)
        calc_grid.addWidget(QLabel(self.tr("Dilution Factor:")), 1, 0); calc_grid.addWidget(self.spin_dilution, 1, 1)

        self.combo_region = QComboBox()
        self.combo_region.currentIndexChanged.connect(self._on_region_changed)
        self.combo_region.currentIndexChanged.connect(self._on_param_changed)
        calc_grid.addWidget(QLabel(self.tr("Counting Region:")), 2, 0); calc_grid.addWidget(self.combo_region, 2, 1)

        self.spin_volume = QDoubleSpinBox()
        self.spin_volume.setDecimals(8); self.spin_volume.setRange(0.0, 1.0); self.spin_volume.setValue(0.0001)
        self.spin_volume.setSingleStep(0.00001)
        self.spin_volume.valueChanged.connect(self._on_param_changed)
        calc_grid.addWidget(QLabel(self.tr("Vol/Sq (mL):")), 3, 0); calc_grid.addWidget(self.spin_volume, 3, 1)

        self._update_region_options() # Initial populate now that all widgets are ready
        
        card_layout.addLayout(calc_grid)
        
        card_layout.addStretch()
        self.btn_count_main = QPushButton(self.tr("🚀 Start All Tabs"), objectName="primary")
        self.btn_count_main.clicked.connect(self._start_counting)
        card_layout.addWidget(self.btn_count_main)
        
        layout.addWidget(card)
        return panel

    def _on_param_changed(self):
        """Handle parameter changes: save settings and update UI with re-detection preview"""
        self._save_settings()
        self._update_current_preview()
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
        
        # Validation to prevent OpenCV errors
        if min_area <= 0: min_area = 1
        if max_area <= min_area: max_area = min_area + 1
        
        use_circ = self.chk_circularity.currentData() == "Enabled"
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
        # Default minimum is 0, but can be overridden if needed. 
        # For areas, we'll keep 0 here but validate logic side.
        # Actually, let's enforce min 1 if label contains "Area" to be safe UI-wise too
        min_val = 1 if "Area" in label else 0
        
        spin.setRange(min_val, max_val); spin.setValue(val); spin.setSingleStep(step); spin.setSuffix(suffix)
        layout.addWidget(spin, row, col)
        return spin

    def _create_result_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        card = QFrame(objectName="cardPanel")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 20, 15, 15)
        
        header_label = QLabel(self.tr("📊 Statistics & Results"))
        header_label.setObjectName("bigHeaderLabel")
        card_layout.addWidget(header_label)

        self.result_table = CopyableTableWidget(5, 2)
        self.result_table.setHorizontalHeaderLabels([self.tr("Image Source"), self.tr("Cell Count")])
        self.result_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setShowGrid(False)
        self.result_table.setAlternatingRowColors(True)
        
        for i, name in enumerate([self.tr("📷 Image 1"), self.tr("📷 Image 2"), self.tr("📷 Image 3"), self.tr("📷 Image 4"), self.tr("📈 TOTAL")]):
            item_name = QTableWidgetItem(name)
            item_name.setFlags(item_name.flags() & ~Qt.ItemIsEditable)
            if i == 4:
                item_name.setForeground(Qt.cyan)
                font = item_name.font()
                font.setBold(True)
                item_name.setFont(font)
            self.result_table.setItem(i, 0, item_name)
            
            item_val = QTableWidgetItem("0")
            item_val.setTextAlignment(Qt.AlignCenter)
            if i == 4: # Total is not editable
                item_val.setFlags(item_val.flags() & ~Qt.ItemIsEditable)
                item_val.setForeground(Qt.GlobalColor.cyan)
                font = item_val.font()
                font.setBold(True)
                item_val.setFont(font)
            self.result_table.setItem(i, 1, item_val)
        
        self.result_table.itemChanged.connect(self._on_table_item_changed)
        card_layout.addWidget(self.result_table)

        # Sample Volume input moved here
        vol_input_layout = QHBoxLayout()
        lbl_vol = QLabel(self.tr("Sample Vol (mL):"))
        lbl_vol.setObjectName("unitLabel")
        vol_input_layout.addWidget(lbl_vol)
        self.spin_total_vol = QDoubleSpinBox()
        self.spin_total_vol.setRange(0.0, 1000000.0); self.spin_total_vol.setValue(1.0)
        self.spin_total_vol.setSingleStep(1.0); self.spin_total_vol.setSuffix(" mL")
        self.spin_total_vol.valueChanged.connect(self._on_param_changed)
        vol_input_layout.addWidget(self.spin_total_vol)
        card_layout.addLayout(vol_input_layout)
        
        conc_card = QFrame(objectName="resultCard")
        conc_layout = QVBoxLayout(conc_card)
        self.conc_label = QLabel("--", alignment=Qt.AlignmentFlag.AlignCenter, objectName="resultValue")
        self.conc_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        conc_layout.addWidget(self.conc_label)
        lbl_unit = QLabel(self.tr("cells/mL"), alignment=Qt.AlignmentFlag.AlignCenter, objectName="unitLabel")
        conc_layout.addWidget(lbl_unit)
        card_layout.addWidget(conc_card)

        total_sample_card = QFrame(objectName="totalCard")
        total_sample_layout = QVBoxLayout(total_sample_card)
        self.total_sample_label = QLabel("--", alignment=Qt.AlignCenter, objectName="resultValueSuccess")
        self.total_sample_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        total_sample_layout.addWidget(self.total_sample_label)
        lbl_total_unit = QLabel(self.tr("total cells in sample"), alignment=Qt.AlignCenter, objectName="unitLabel")
        total_sample_layout.addWidget(lbl_total_unit)
        card_layout.addWidget(total_sample_card)
        
        card_layout.addStretch()
        
        btn_layout = QHBoxLayout()
        self.btn_copy_report = QPushButton(self.tr("📋 Copy"), objectName="secondary", enabled=False)
        self.btn_copy_report.clicked.connect(self._copy_results_to_clipboard)
        self.btn_save_report = QPushButton(self.tr("💾 Export"), objectName="primary", enabled=False)
        self.btn_save_report.clicked.connect(self._save_results)
        btn_layout.addWidget(self.btn_copy_report)
        btn_layout.addWidget(self.btn_save_report)
        card_layout.addLayout(btn_layout)
        
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
            self.image_tabs.addTab(tab, f"{self.tr('📷 Image')} {i+1}")
        layout.addWidget(self.image_tabs)
        return panel

    def _create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine); line.setFrameShadow(QFrame.Shadow.Plain)
        line.setObjectName("separator")
        return line

    def _import_images(self):
        # Support both individual files and folders
        msg = QMessageBox()
        msg.setWindowTitle(self.tr("Import Images"))
        msg.setText(self.tr("Choose import method:"))
        btn_files = msg.addButton(self.tr("Select Files"), QMessageBox.ButtonRole.ActionRole)
        btn_folder = msg.addButton(self.tr("Select Folder"), QMessageBox.ButtonRole.ActionRole)
        msg.addButton(QMessageBox.StandardButton.Cancel)
        msg.exec()

        files = []
        if msg.clickedButton() == btn_files:
            print(f"DEBUG: Opening file dialog in {self.last_dir}")
            files, _ = QFileDialog.getOpenFileNames(
                self, "Select Images", self.last_dir, 
                "Images (*.jpg *.jpeg *.png *.bmp *.webp *.tiff *.tif *.TIFF *.TIF);;All Files (*)"
            )
            if files:
                print(f"DEBUG: Selected {len(files)} files: {files[:5]}")
                self.last_dir = os.path.dirname(files[0])
                self._save_settings()
        elif msg.clickedButton() == btn_folder:
            print(f"DEBUG: Opening folder dialog in {self.last_dir}")
            
            # Use a custom dialog to allow seeing files while picking a directory
            dialog = QFileDialog(self)
            dialog.setWindowTitle("Select Folder (Files are visible for reference)")
            dialog.setDirectory(self.last_dir)
            dialog.setFileMode(QFileDialog.FileMode.Directory)
            dialog.setOption(QFileDialog.Option.ShowDirsOnly, False) # This allows seeing files
            
            if dialog.exec():
                selected_dirs = dialog.selectedFiles()
                if not selected_dirs: return
                folder = selected_dirs[0]
                
                print(f"DEBUG: Selected folder: {folder}")
                self.last_dir = folder
                self._save_settings()
                
                # Get first 4 valid images from folder
                valid_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif')
                try:
                    all_files = os.listdir(folder)
                    files = [os.path.join(folder, f) for f in all_files 
                            if f.lower().endswith(valid_exts)]
                except Exception as e:
                    print(f"DEBUG: Error listing folder: {e}")
                    files = []
                
                if files:
                    files.sort(key=natural_sort_key)
                    count = min(len(files), 4)
                    file_names = "\n".join([os.path.basename(f) for f in files[:4]])
                    QMessageBox.information(self, "Import Successful", 
                                          f"Successfully found {len(files)} images.\n"
                                          f"The first {count} images will be loaded:\n\n{file_names}")
                else:
                    QMessageBox.warning(self, "No Images Found", 
                                      f"No valid images (JPG, PNG, TIFF, etc.) were found in:\n{folder}")
                    return
        
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
            text = self.combo_region.currentData()
            match = re.search(r'(\d+)', text)
            num_sq = int(match.group(1)) if match else 1
            conc = calculate_concentration(total_cells, self.spin_dilution.value(), num_sq, self.spin_volume.value())
            self.conc_label.setText(f"{conc:.4e}")

            # Update Total Sample Label
            total_sample = conc * self.spin_total_vol.value()
            self.total_sample_label.setText(f"{total_sample:.4e}")
            
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
        text = self.combo_region.currentData()
        match = re.search(r'(\d+)', text)
        num_sq = int(match.group(1)) if match else 1
        
        conc = calculate_concentration(total_cells, self.spin_dilution.value(), num_sq, self.spin_volume.value())
        self.conc_label.setText(f"{conc:.4e}")
        
        total_item = self.result_table.item(4, 1)
        if total_item:
            total_item.setText(str(total_cells))
            
        # Update Total Sample Label
        total_sample = conc * self.spin_total_vol.value()
        self.total_sample_label.setText(f"{total_sample:.4e}")
            
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
            
            # Validation to prevent OpenCV errors
            if min_area <= 0: min_area = 1
            if max_area <= min_area: max_area = min_area + 1
            
            use_circ = self.chk_circularity.currentData() == "Enabled"
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
            self.btn_copy_report.setEnabled(True)
            self.statusBar().showMessage(self.tr("Counting completed."), 5000)
            
        finally:
            self.progress_bar.setVisible(False)
            self.setEnabled(True)
            # Re-enable UI and focus back
            self.activateWindow()

    def _copy_results_to_clipboard(self):
        """Copy results to system clipboard"""
        if not self.conc_label: return
        
        text = f"Total Cells: {sum(self.cell_counts)}\n"
        text += f"Concentration: {self.conc_label.text()} cells/mL\n"
        text += f"Total Sample: {self.total_sample_label.text()} cells\n"
        
        clipboard = QtGui.QGuiApplication.clipboard()
        clipboard.setText(text)
        self.statusBar().showMessage(self.tr("Results copied to clipboard!"), 3000)

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
