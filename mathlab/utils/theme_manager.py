import os
import json
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

SETTINGS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'settings.json'
)

def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load settings: {e}")
    return {}

def save_settings(settings: dict) -> None:
    try:
        current = load_settings()
        current.update(settings)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(current, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save settings: {e}")

THEMES = {
    'light': {
        'name': 'Light',
        'background': '#ffffff',
        'foreground': '#0b1c30',
        'panel_bg': '#f5f5f5',
        'panel_border': '#d3e4fe',
        'accent': '#004ac6',
        'secondary': '#4b41e1',
        'success': '#22c55e',
        'warning': '#eab308',
        'error': '#ba1a1a',
        'console_bg': '#1e1e1e',
        'console_fg': '#d4d4d4',
        'point_color': '#004ac6',
        'segment_color': '#4b41e1',
        'circle_color': '#006058',
        'polygon_color': '#9333ea',
    },
    'dark': {
        'name': 'Dark',
        'background': '#1e1e1e',
        'foreground': '#d4d4d4',
        'panel_bg': '#2d2d2d',
        'panel_border': '#404040',
        'accent': '#3b82f6',
        'secondary': '#8b5cf6',
        'success': '#22c55e',
        'warning': '#eab308',
        'error': '#ef4444',
        'console_bg': '#0d0d0d',
        'console_fg': '#d4d4d4',
        'point_color': '#3b82f6',
        'segment_color': '#8b5cf6',
        'circle_color': '#14b8a6',
        'polygon_color': '#a855f7',
    },
    'sepia': {
        'name': 'Sepia',
        'background': '#f4ecd8',
        'foreground': '#5c4b37',
        'panel_bg': '#e8dcc8',
        'panel_border': '#c9b896',
        'accent': '#8b5a2b',
        'secondary': '#6b4423',
        'success': '#567d46',
        'warning': '#d4a017',
        'error': '#b83b1e',
        'console_bg': '#3d3225',
        'console_fg': '#e8dcc8',
        'point_color': '#8b5a2b',
        'segment_color': '#6b4423',
        'circle_color': '#567d46',
        'polygon_color': '#9b4dca',
    },
}

def get_current_theme():
    # Force dark theme to match our modern fluent dark styles.qss
    return 'dark'

def set_theme(theme_name):
    if theme_name not in THEMES:
        return False

    app = QApplication.instance()
    theme = THEMES[theme_name]

    palette = QPalette()

    palette.setColor(QPalette.Window, QColor(theme['background']))
    palette.setColor(QPalette.WindowText, QColor(theme['foreground']))
    palette.setColor(QPalette.Base, QColor(theme['panel_bg']))
    palette.setColor(QPalette.AlternateBase, QColor(theme['panel_bg']))
    palette.setColor(QPalette.ToolTipBase, QColor(theme['accent']))
    palette.setColor(QPalette.ToolTipText, QColor(theme['background']))
    palette.setColor(QPalette.Text, QColor(theme['foreground']))
    palette.setColor(QPalette.Button, QColor(theme['panel_bg']))
    palette.setColor(QPalette.ButtonText, QColor(theme['foreground']))
    palette.setColor(QPalette.BrightText, QColor(theme['error']))
    palette.setColor(QPalette.Highlight, QColor(theme['accent']))
    palette.setColor(QPalette.HighlightedText, QColor(theme['background']))

    app.setPalette(palette)
    app.setProperty('current_theme', theme_name)

    app.setStyleSheet(f"""
        QMainWindow, QDialog {{
            background-color: {theme['background']};
            color: {theme['foreground']};
        }}
        QLabel {{
            color: {theme['foreground']};
        }}
        QDockWidget {{
            background-color: {theme['panel_bg']};
            color: {theme['foreground']};
            border: 1px solid {theme['panel_border']};
        }}
        QDockWidget::title {{
            background-color: {theme['panel_bg']};
            border: 1px solid {theme['panel_border']};
            padding: 4px;
        }}
        QMenuBar {{
            background-color: {theme['panel_bg']};
            color: {theme['foreground']};
        }}
        QMenuBar::item:selected {{
            background-color: {theme['accent']};
        }}
        QMenu {{
            background-color: {theme['panel_bg']};
            color: {theme['foreground']};
            border: 1px solid {theme['panel_border']};
        }}
        QMenu::item:selected {{
            background-color: {theme['accent']};
        }}
        QToolBar {{
            background-color: {theme['panel_bg']};
            border: 1px solid {theme['panel_border']};
        }}
        QStatusBar {{
            background-color: {theme['panel_bg']};
            color: {theme['foreground']};
        }}
        QTreeWidget {{
            background-color: {theme['background']};
            color: {theme['foreground']};
            border: 1px solid {theme['panel_border']};
        }}
        QPlainTextEdit {{
            background-color: {theme['console_bg']};
            color: {theme['console_fg']};
        }}
        QLineEdit, QComboBox, QSpinBox {{
            background-color: {theme['panel_bg']};
            color: {theme['foreground']};
            border: 1px solid {theme['panel_border']};
        }}
        QComboBox QAbstractItemView {{
            background-color: {theme['panel_bg']};
            color: {theme['foreground']};
            selection-background-color: {theme['accent']};
        }}
        QPushButton {{
            background-color: {theme['panel_bg']};
            color: {theme['foreground']};
            border: 1px solid {theme['panel_border']};
            padding: 4px 12px;
        }}
    """)

    save_settings({'theme': theme_name})
    return True

def get_theme_colors(theme_name=None):
    if theme_name is None:
        theme_name = get_current_theme()
    return THEMES.get(theme_name, THEMES['light'])