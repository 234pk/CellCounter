MAIN_STYLE = """
    QMainWindow { background-color: #0f0f1a; }
    QWidget {
        color: #e0e0e0;
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        font-size: 13px;
    }
    QFrame#cardPanel {
        background-color: #1a1a2e;
        border: 2px solid #2a2a4a;
        border-radius: 10px;
    }
    QGroupBox {
        font-weight: bold;
        border: 2px solid #2a2a4a;
        border-radius: 10px;
        margin-top: 12px;
        padding-top: 12px;
        background-color: #1a1a2e;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 8px;
        color: #00d4ff;
        font-size: 14px;
    }
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0078d7, stop:1 #00d4ff);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: bold;
        min-width: 100px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a86d9, stop:1 #00e5ff);
    }
    QPushButton:disabled {
        background: #3a3a4a;
        color: #666;
    }
    QPushButton#danger {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #d93025, stop:1 #ff6b6b);
    }
    QPushButton#secondary {
        background: #2a2a4a;
        border: 1px solid #3a3a5e;
    }
    QSpinBox, QDoubleSpinBox {
        background-color: #1a1a2e;
        border: 2px solid #2a2a4a;
        border-radius: 6px;
        padding: 8px 12px;
        color: #e0e0e0;
    }
    QSpinBox:focus, QDoubleSpinBox:focus {
        border-color: #00d4ff;
    }
    QComboBox {
        background-color: #2a2a4a;
        border: 1px solid #3a3a6a;
        border-radius: 4px;
        padding: 4px 10px;
        color: #ffffff;
    }
    QComboBox:hover {
        background-color: #35355a;
        border: 1px solid #00d4ff;
    }
    QComboBox::drop-down {
        border: none;
        width: 24px;
    }
    QComboBox QAbstractItemView {
        background-color: #1a1a2e;
        border: 1px solid #3a3a6a;
        selection-background-color: #00d4ff;
        selection-color: #ffffff;
        color: #e0e0e0;
        outline: none;
    }
    QPushButton#mode-active {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00d4ff, stop:1 #0078d7);
        border: 2px solid #ffffff;
    }
    QPushButton#mode-inactive {
        background: #2a2a4a;
        color: #888;
        border: 1px solid #3a3a5e;
    }
    QTableWidget {
        background-color: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 8px;
        gridline-color: #2a2a4a;
        selection-background-color: #2a2a4a;
        selection-color: #00d4ff;
    }
    QTableWidget::item {
        padding: 8px;
        border-bottom: 1px solid #2a2a4a;
    }
    QHeaderView::section {
        background-color: #2a2a4a;
        color: #00d4ff;
        padding: 8px;
        font-weight: bold;
        border: none;
        border-bottom: 2px solid #00d4ff;
    }
    QProgressBar {
        background-color: #1a1a2e;
        border: 2px solid #2a2a4a;
        border-radius: 8px;
        text-align: center;
        color: white;
    }
    QProgressBar::chunk {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0078d7, stop:1 #00d4ff);
        border-radius: 6px;
    }
    QTabWidget::pane {
        border: 2px solid #2a2a4a;
        background-color: #1a1a2e;
        border-radius: 8px;
    }
    QTabBar::tab {
        background-color: #2a2a4a;
        color: #888;
        padding: 8px 20px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }
    QTabBar::tab:selected {
        background-color: #0078d7;
        color: white;
        font-weight: bold;
    }
"""

VIEWER_STYLE = """
    QLabel {
        background-color: #1a1a2e;
        border: 2px solid #3a3a5e;
        border-radius: 8px;
    }
    QLabel:hover {
        border-color: #00d4ff;
    }
"""
