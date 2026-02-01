
THEMES = {
    "Dark": {
        "bg_main": "#0f0f1a",
        "text_main": "#e0e0e0",
        "bg_panel": "#1a1a2e",
        "border_panel": "#2a2a4a",
        "accent": "#00d4ff",
        "accent_hover": "#00e5ff",
        "accent_gradient_start": "#0078d7",
        "accent_gradient_end": "#00d4ff",
        "danger_start": "#d93025",
        "danger_end": "#ff6b6b",
        "secondary_bg": "#2a2a4a",
        "secondary_border": "#3a3a5e",
        "input_bg": "#1a1a2e",
        "input_border": "#2a2a4a",
        "text_muted": "#888",
        "text_success": "#00ff88",
        "text_warning": "#ffcc00",
        "table_grid": "#2a2a4a",
        "tab_bg": "#2a2a4a",
        "tab_selected": "#0078d7",
        "viewer_bg": "#1e1e1e",
        "viewer_border": "#505050"
    },
    "Midnight": {
        "bg_main": "#000000",
        "text_main": "#e0e0e0",
        "bg_panel": "#0a0a12",
        "border_panel": "#1f1f33",
        "accent": "#7b68ee",
        "accent_hover": "#9370db",
        "accent_gradient_start": "#483d8b",
        "accent_gradient_end": "#7b68ee",
        "danger_start": "#8b0000",
        "danger_end": "#ff4500",
        "secondary_bg": "#1f1f33",
        "secondary_border": "#2f2f4f",
        "input_bg": "#0a0a12",
        "input_border": "#1f1f33",
        "text_muted": "#666",
        "text_success": "#00ff88",
        "text_warning": "#ffd700",
        "table_grid": "#1f1f33",
        "tab_bg": "#1f1f33",
        "tab_selected": "#483d8b",
        "viewer_bg": "#050505",
        "viewer_border": "#333333"
    },
    "Light": {
        "bg_main": "#f5f5f7",
        "text_main": "#333333",
        "bg_panel": "#ffffff",
        "border_panel": "#d1d1d6",
        "accent": "#007aff",
        "accent_hover": "#0051a8",
        "accent_gradient_start": "#007aff",
        "accent_gradient_end": "#3395ff",
        "danger_start": "#ff3b30",
        "danger_end": "#ff6b6b",
        "secondary_bg": "#e5e5ea",
        "secondary_border": "#c7c7cc",
        "input_bg": "#ffffff",
        "input_border": "#d1d1d6",
        "text_muted": "#666666",
        "text_success": "#008844",
        "text_warning": "#f57f17",
        "table_grid": "#e5e5ea",
        "tab_bg": "#e5e5ea",
        "tab_selected": "#007aff",
        "viewer_bg": "#f0f0f0",
        "viewer_border": "#c7c7cc"
    },
    "Scientific": {
        "bg_main": "#ffffff",
        "text_main": "#2c3e50",
        "bg_panel": "#f8f9fa",
        "border_panel": "#dfe6e9",
        "accent": "#0984e3",
        "accent_hover": "#74b9ff",
        "accent_gradient_start": "#0984e3",
        "accent_gradient_end": "#74b9ff",
        "danger_start": "#d63031",
        "danger_end": "#ff7675",
        "secondary_bg": "#dfe6e9",
        "secondary_border": "#b2bec3",
        "input_bg": "#ffffff",
        "input_border": "#dfe6e9",
        "text_muted": "#636e72",
        "text_success": "#00b894",
        "text_warning": "#e67e22",
        "table_grid": "#dfe6e9",
        "tab_bg": "#dfe6e9",
        "tab_selected": "#0984e3",
        "viewer_bg": "#f8f9fa",
        "viewer_border": "#b2bec3"
    }
}

MAIN_STYLE_TEMPLATE = """
    QMainWindow {{ background-color: {bg_main}; }}
    QWidget {{
        color: {text_main};
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        font-size: 13px;
    }}
    QFrame#cardPanel {{
        background-color: {bg_panel};
        border: 2px solid {border_panel};
        border-radius: 10px;
    }}
    QGroupBox {{
        font-weight: bold;
        border: 2px solid {border_panel};
        border-radius: 10px;
        margin-top: 12px;
        padding-top: 12px;
        background-color: {bg_panel};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 8px;
        color: {accent};
        font-size: 14px;
    }}
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {accent_gradient_start}, stop:1 {accent_gradient_end});
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: bold;
        min-width: 100px;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {accent}, stop:1 {accent_hover});
    }}
    QPushButton:disabled {{
        background: {secondary_border};
        color: {text_muted};
    }}
    QPushButton#danger {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {danger_start}, stop:1 {danger_end});
    }}
    QPushButton#secondary {{
        background: {secondary_bg};
        border: 1px solid {secondary_border};
        color: {text_main};
    }}
    QSpinBox, QDoubleSpinBox {{
        background-color: {input_bg};
        border: 2px solid {input_border};
        border-radius: 6px;
        padding: 8px 12px;
        color: {text_main};
    }}
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {accent};
    }}
    QComboBox {{
        background-color: {secondary_bg};
        border: 1px solid {secondary_border};
        border-radius: 4px;
        padding: 4px 10px;
        color: {text_main};
    }}
    QComboBox:hover {{
        background-color: {secondary_border};
        border: 1px solid {accent};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {input_bg};
        border: 1px solid {secondary_border};
        selection-background-color: {accent};
        selection-color: white;
        color: {text_main};
        outline: none;
    }}
    QPushButton#mode-active {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {accent_gradient_end}, stop:1 {accent_gradient_start});
        border: 2px solid white;
    }}
    QPushButton#mode-inactive {{
        background: {secondary_bg};
        color: {text_muted};
        border: 1px solid {secondary_border};
    }}
    QTableWidget {{
        background-color: {input_bg};
        border: 1px solid {input_border};
        border-radius: 8px;
        gridline-color: {table_grid};
        selection-background-color: {secondary_bg};
        selection-color: {accent};
    }}
    QTableWidget::item {{
        padding: 8px;
        border-bottom: 1px solid {input_border};
    }}
    QHeaderView::section {{
        background-color: {secondary_bg};
        color: {accent};
        padding: 8px;
        font-weight: bold;
        border: none;
        border-bottom: 2px solid {accent};
    }}
    QProgressBar {{
        background-color: {input_bg};
        border: 2px solid {input_border};
        border-radius: 8px;
        text-align: center;
        color: {text_main};
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {accent_gradient_start}, stop:1 {accent_gradient_end});
        border-radius: 6px;
    }}
    QTabWidget::pane {{
        border: 2px solid {border_panel};
        background-color: {bg_panel};
        border-radius: 8px;
    }}
    QTabBar::tab {{
        background-color: {tab_bg};
        color: {text_muted};
        padding: 8px 20px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }}
    QTabBar::tab:selected {{
        background-color: {tab_selected};
        color: white;
        font-weight: bold;
    }}
    
    /* New Unified Styles */
    QLabel#titleLabel {{
        color: {accent};
        font-weight: bold;
        font-size: 16px;
        margin-right: 15px;
    }}
    QLabel#modeLabel {{
        color: {text_muted};
        font-weight: bold;
        margin-left: 10px;
    }}
    QLabel#headerLabel {{
        color: {accent};
        font-weight: bold;
    }}
    QLabel#bigHeaderLabel {{
        color: {accent};
        font-weight: bold;
        font-size: 16px;
        margin-bottom: 10px;
    }}
    QFrame#resultCard {{
        background-color: {input_bg};
        border-radius: 10px;
        border: 1px solid {input_border};
    }}
    QFrame#totalCard {{
        background-color: {input_bg};
        border-radius: 10px;
        border: 1px solid {input_border};
        margin-top: 5px;
    }}
    QLabel#resultValue {{
        font-size: 32px;
        font-weight: bold;
        color: {accent};
        border: none;
    }}
    QLabel#resultValueSuccess {{
        font-size: 24px;
        font-weight: bold;
        color: {text_success};
        border: none;
    }}
    QLabel#unitLabel {{
        color: {text_muted};
        font-size: 12px;
        border: none;
    }}
    QFrame#separator {{
        background-color: {border_panel};
        max-height: 1px;
    }}
    
    /* Popups and Menus */
    QMessageBox {{
        background-color: {bg_panel};
        border: 1px solid {border_panel};
    }}
    QMessageBox QLabel {{
        color: {text_main};
    }}
    QMenu {{
        background-color: {bg_panel};
        border: 1px solid {border_panel};
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 24px;
        color: {text_main};
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {accent};
        color: white;
    }}
    QMenu::separator {{
        height: 1px;
        background: {border_panel};
        margin: 4px 0px;
    }}
    QToolTip {{
        background-color: {bg_panel};
        color: {text_main};
        border: 1px solid {accent};
        padding: 4px;
    }}
"""

VIEWER_STYLE_TEMPLATE = """
    QLabel {{
        background-color: {viewer_bg};
        border: 2px solid {viewer_border};
        border-radius: 8px;
    }}
    QLabel:hover {{
        border-color: {accent};
    }}
"""

def get_main_style(theme="Dark"):
    params = THEMES.get(theme, THEMES["Dark"])
    return MAIN_STYLE_TEMPLATE.format(**params)

def get_viewer_style(theme="Dark"):
    params = THEMES.get(theme, THEMES["Dark"])
    return VIEWER_STYLE_TEMPLATE.format(**params)

# Maintain backward compatibility
MAIN_STYLE = get_main_style("Dark")
VIEWER_STYLE = get_viewer_style("Dark")
