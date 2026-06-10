"""
ui/preferences_dialog.py
------------------------
MathLab Preferences / Settings dialog.

Layout
~~~~~~
  Left  : QTabWidget (West / sidebar mode) — 5 tabs
  Right : QScrollArea + QFormLayout per page
  Bottom: [Cancel]  [Apply]  [OK]

Signals exported to main window
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  theme_changed(str)                  — theme key e.g. "dark"
  accent_color_changed(str)           — hex colour string
  font_changed(str, int)              — family, pt-size
  language_changed(str)               — lang code e.g. "zh"
  graphics_settings_changed(dict)
  console_settings_changed(dict)
  shortcuts_changed(dict)
  advanced_settings_changed(dict)
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QFormLayout, QComboBox, QPushButton, QFontComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QSlider, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QMessageBox, QScrollArea,
    QFrame,
)

try:
    from ..utils.i18n_manager import t, get_i18n, SUPPORTED_LANGUAGES
    from ..utils.theme_manager import THEMES, set_theme, get_current_theme
except ImportError:
    from utils.i18n_manager import t, get_i18n, SUPPORTED_LANGUAGES
    from utils.theme_manager import THEMES, set_theme, get_current_theme


_TAB_STYLE = """
QTabWidget::pane {
    border: none;
    border-left: 1px solid #c3c6d7;
    background: #ffffff;
}
QTabBar {
    background: #f8f9ff;
}
QTabBar::tab {
    padding: 12px 20px;
    text-align: left;
    min-width: 180px;
    font-size: 13px;
    font-weight: 400;
    color: #434655;
    border-right: 1px solid #c3c6d7;
    border-bottom: 1px solid #c3c6d7;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #004ac6;
    font-weight: 600;
    border-left: 3px solid #004ac6;
    border-right: none;
}
QTabBar::tab:hover:!selected {
    background: #eff4ff;
}
"""

_ACCENT_COLORS = [
    "#004ac6",
    "#10B981",
    "#8B5CF6",
    "#F59E0B",
    "#EF4444",
]


class PreferencesDialog(QDialog):
    theme_changed = Signal(str)
    accent_color_changed = Signal(str)
    font_changed = Signal(str, int)
    language_changed = Signal(str)
    graphics_settings_changed = Signal(dict)
    console_settings_changed = Signal(dict)
    shortcuts_changed = Signal(dict)
    advanced_settings_changed = Signal(dict)

    def __init__(self, parent=None, initial_settings: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle(t("preferences.title"))
        self.setMinimumSize(700, 500)
        self.resize(800, 560)

        self.settings: dict = initial_settings or self._default_settings()

        self._build_ui()
        self._load_settings()

        get_i18n().add_language_change_listener(self._on_lang_changed_extern)

    @staticmethod
    def _default_settings() -> dict:
        return {
            "theme":             get_current_theme(),
            "accent":            "#004ac6",
            "ui_font":           "Segoe UI",
            "ui_font_size":      10,
            "canvas_bg":         "grid",
            "line_width":        1.5,
            "point_size":        4,
            "aa_enabled":        True,
            "anim_speed":        50,
            "console_font":      "Consolas",
            "console_font_size": 11,
            "console_history":   1000,
            "autocomplete":      True,
            "hw_accel":          False,
            "autosave_interval": 5,
            "shortcuts": {
                "New Project":  "Ctrl+N",
                "Save":         "Ctrl+S",
                "Undo":         "Ctrl+Z",
                "Redo":         "Ctrl+Shift+Z",
                "Clear Canvas": "Ctrl+Del",
                "Select Mode":  "Esc",
                "Execute Code": "Shift+Enter",
            },
        }

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header.setStyleSheet("background: #f8f9ff; border-bottom: 1px solid #c3c6d7;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 12, 24, 12)
        header_layout.setSpacing(12)

        title_label = QLabel(t("preferences.title"))
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #0b1c30;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        close_btn = QPushButton()
        close_btn.setText("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(
            "QPushButton {"
            "  background: transparent;"
            "  border: none;"
            "  font-size: 16px;"
            "  color: #737686;"
            "}"
            "QPushButton:hover {"
            "  background: #eff4ff;"
            "  color: #0b1c30;"
            "  border-radius: 4px;"
            "}"
        )
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)

        root.addWidget(header)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.setStyleSheet(_TAB_STYLE)

        self.tabs.addTab(self._page_appearance(), t("preferences.appearance"))
        self.tabs.addTab(self._page_graphics(),   t("preferences.graphics"))
        self.tabs.addTab(self._page_console(),    t("preferences.console_tab"))
        self.tabs.addTab(self._page_shortcuts(),  t("preferences.shortcuts"))
        self.tabs.addTab(self._page_advanced(),   t("preferences.advanced"))

        body_layout.addWidget(self.tabs, 1)
        root.addWidget(body, 1)

        bar = QWidget()
        bar.setStyleSheet("background: #f8f9ff; border-top: 1px solid #c3c6d7;")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(24, 16, 24, 16)
        bar_layout.setSpacing(8)

        self.btn_cancel = QPushButton(t("dialogs.cancel"))
        self.btn_cancel.setStyleSheet(
            "QPushButton {"
            "  background: transparent;"
            "  border: 1px solid #c3c6d7;"
            "  color: #0b1c30;"
            "  padding: 8px 20px;"
            "  border-radius: 4px;"
            "  font-size: 14px;"
            "}"
            "QPushButton:hover {"
            "  background: #eff4ff;"
            "}"
        )

        self.btn_apply  = QPushButton(t("preferences.apply"))
        self.btn_apply.setEnabled(False)
        self.btn_apply.setStyleSheet(
            "QPushButton {"
            "  background: transparent;"
            "  border: 1px solid #c3c6d7;"
            "  color: #737686;"
            "  padding: 8px 20px;"
            "  border-radius: 4px;"
            "  font-size: 14px;"
            "}"
            "QPushButton:hover {"
            "  background: #eff4ff;"
            "}"
        )

        self.btn_ok     = QPushButton(t("preferences.ok"))
        self.btn_ok.setDefault(True)
        self.btn_ok.setStyleSheet(
            "QPushButton {"
            "  background: #004ac6;"
            "  color: white;"
            "  border: none;"
            "  padding: 8px 24px;"
            "  border-radius: 4px;"
            "  font-size: 14px;"
            "  font-weight: 600;"
            "}"
            "QPushButton:hover {"
            "  background: #2563eb;"
            "}"
        )

        bar_layout.addStretch()
        bar_layout.addWidget(self.btn_cancel)
        bar_layout.addWidget(self.btn_apply)
        bar_layout.addWidget(self.btn_ok)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_apply.clicked.connect(self._apply_settings)
        self.btn_ok.clicked.connect(self._on_ok)

        root.addWidget(bar)

    @staticmethod
    def _scroll(inner: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(inner)
        return scroll

    def _create_section_header(self, title: str) -> QLabel:
        header = QLabel(title)
        header.setStyleSheet(
            "font-size: 11px; font-weight: 700; letter-spacing: 0.05em; "
            "text-transform: uppercase; color: #004ac6; padding-bottom: 8px; "
            "border-bottom: 1px solid #c3c6d7; margin-bottom: 16px;"
        )
        return header

    def _page_appearance(self) -> QScrollArea:
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setSpacing(16)
        section_layout.addWidget(self._create_section_header(t("preferences.appearance")))

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignLeft)

        theme_label = QLabel(t("preferences.theme"))
        theme_label.setStyleSheet("font-size: 12px; color: #434655;")
        self.theme_combo = QComboBox()
        self.theme_combo.setStyleSheet(
            "min-height: 32px; padding: 0 10px; border: 1px solid #c3c6d7; "
            "border-radius: 4px; background: white;"
        )
        for key, data in THEMES.items():
            self.theme_combo.addItem(data["name"], key)
        form.addRow(theme_label, self.theme_combo)

        accent_label = QLabel(t("preferences.accent_color"))
        accent_label.setStyleSheet("font-size: 12px; color: #434655;")
        accent_row = QHBoxLayout()
        accent_row.setSpacing(8)
        self.accent_btns: list[tuple[str, QPushButton]] = []
        for color in _ACCENT_COLORS:
            btn = QPushButton()
            btn.setFixedSize(26, 26)
            btn.setCheckable(True)
            btn.setStyleSheet(
                f"background-color:{color}; border-radius:13px; border:2px solid transparent;"
            )
            btn.clicked.connect(lambda _checked, c=color: self._set_accent(c))
            accent_row.addWidget(btn)
            self.accent_btns.append((color, btn))
        accent_row.addStretch()
        form.addRow(accent_label, accent_row)

        font_label = QLabel(t("preferences.interface_font"))
        font_label.setStyleSheet("font-size: 12px; color: #434655;")
        self.ui_font_combo = QFontComboBox()
        self.ui_font_size_spin = QSpinBox()
        self.ui_font_size_spin.setRange(8, 24)
        self.ui_font_size_spin.setSuffix(" pt")
        self.ui_font_size_spin.setStyleSheet(
            "min-height: 32px; padding: 0 6px; border: 1px solid #c3c6d7; "
            "border-radius: 4px; background: white;"
        )
        font_row = QHBoxLayout()
        font_row.addWidget(self.ui_font_combo, 1)
        font_row.addWidget(self.ui_font_size_spin)
        form.addRow(font_label, font_row)

        bg_label = QLabel(t("preferences.canvas_background"))
        bg_label.setStyleSheet("font-size: 12px; color: #434655;")
        self.bg_combo = QComboBox()
        self.bg_combo.addItem(t("preferences.canvas_bg_grid"),  "grid")
        self.bg_combo.addItem(t("preferences.canvas_bg_blank"), "blank")
        self.bg_combo.addItem(t("preferences.canvas_bg_polar"), "polar")
        self.bg_combo.setStyleSheet(
            "min-height: 32px; padding: 0 10px; border: 1px solid #c3c6d7; "
            "border-radius: 4px; background: white;"
        )
        form.addRow(bg_label, self.bg_combo)

        lang_label = QLabel(t("preferences.language"))
        lang_label.setStyleSheet("font-size: 12px; color: #434655;")
        self.lang_combo = QComboBox()
        for code, display in SUPPORTED_LANGUAGES.items():
            self.lang_combo.addItem(display, code)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_combo_changed)
        self.lang_combo.setStyleSheet(
            "min-height: 32px; padding: 0 10px; border: 1px solid #c3c6d7; "
            "border-radius: 4px; background: white;"
        )
        form.addRow(lang_label, self.lang_combo)

        section_layout.addLayout(form)
        layout.addWidget(section)

        return self._scroll(inner)

    def _page_graphics(self) -> QScrollArea:
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setSpacing(16)
        section_layout.addWidget(self._create_section_header(t("preferences.graphics")))

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(16)

        line_width_label = QLabel(t("preferences.default_line_width"))
        line_width_label.setStyleSheet("font-size: 12px; color: #434655;")
        self.line_width_spin = QDoubleSpinBox()
        self.line_width_spin.setRange(0.1, 10.0)
        self.line_width_spin.setSingleStep(0.1)
        self.line_width_spin.setSuffix(" px")
        self.line_width_spin.setStyleSheet(
            "min-height: 32px; padding: 0 6px; border: 1px solid #c3c6d7; "
            "border-radius: 4px; background: white;"
        )
        form.addRow(line_width_label, self.line_width_spin)

        point_size_label = QLabel(t("preferences.default_point_size"))
        point_size_label.setStyleSheet("font-size: 12px; color: #434655;")
        self.point_size_spin = QSpinBox()
        self.point_size_spin.setRange(1, 20)
        self.point_size_spin.setSuffix(" px")
        self.point_size_spin.setStyleSheet(
            "min-height: 32px; padding: 0 6px; border: 1px solid #c3c6d7; "
            "border-radius: 4px; background: white;"
        )
        form.addRow(point_size_label, self.point_size_spin)

        aa_label = QLabel(t("preferences.rendering"))
        aa_label.setStyleSheet("font-size: 12px; color: #434655;")
        self.aa_check = QCheckBox(t("preferences.antialiasing"))
        form.addRow(aa_label, self.aa_check)

        speed_label = QLabel(t("preferences.animation_speed"))
        speed_label.setStyleSheet("font-size: 12px; color: #434655;")
        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel(t("preferences.slow")))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(10, 200)
        speed_row.addWidget(self.speed_slider, 1)
        speed_row.addWidget(QLabel(t("preferences.fast")))
        form.addRow(speed_label, speed_row)

        snap_label = QLabel(t("preferences.snapping"))
        snap_label.setStyleSheet("font-size: 12px; color: #434655;")
        self.snap_combo = QComboBox()
        self.snap_combo.addItem(t("preferences.snap_grid"), "grid")
        self.snap_combo.addItem(t("preferences.snap_points"), "points")
        self.snap_combo.addItem(t("preferences.snap_off"), "off")
        self.snap_combo.setStyleSheet(
            "min-height: 32px; padding: 0 10px; border: 1px solid #c3c6d7; "
            "border-radius: 4px; background: white;"
        )
        form.addRow(snap_label, self.snap_combo)

        section_layout.addLayout(form)
        layout.addWidget(section)

        return self._scroll(inner)

    def _page_console(self) -> QScrollArea:
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setSpacing(16)
        section_layout.addWidget(self._create_section_header(t("preferences.console_tab")))

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(16)

        font_label = QLabel(t("preferences.console_font"))
        font_label.setStyleSheet("font-size: 12px; color: #434655;")
        self.con_font_combo = QFontComboBox()
        self.con_font_size_spin = QSpinBox()
        self.con_font_size_spin.setRange(8, 30)
        self.con_font_size_spin.setSuffix(" pt")
        self.con_font_size_spin.setStyleSheet(
            "min-height: 32px; padding: 0 6px; border: 1px solid #c3c6d7; "
            "border-radius: 4px; background: white;"
        )
        font_row = QHBoxLayout()
        font_row.addWidget(self.con_font_combo, 1)
        font_row.addWidget(self.con_font_size_spin)
        form.addRow(font_label, font_row)

        color_label = QLabel(t("preferences.color_scheme"))
        color_label.setStyleSheet("font-size: 12px; color: #434655;")
        self.color_scheme_combo = QComboBox()
        self.color_scheme_combo.addItem(t("preferences.scheme_dark"), "dark")
        self.color_scheme_combo.addItem(t("preferences.scheme_light"), "light")
        self.color_scheme_combo.addItem(t("preferences.scheme_system"), "system")
        self.color_scheme_combo.setStyleSheet(
            "min-height: 32px; padding: 0 10px; border: 1px solid #c3c6d7; "
            "border-radius: 4px; background: white;"
        )
        form.addRow(color_label, self.color_scheme_combo)

        history_label = QLabel(t("preferences.history_limit"))
        history_label.setStyleSheet("font-size: 12px; color: #434655;")
        self.history_spin = QSpinBox()
        self.history_spin.setRange(100, 10000)
        self.history_spin.setSingleStep(100)
        self.history_spin.setStyleSheet(
            "min-height: 32px; padding: 0 6px; border: 1px solid #c3c6d7; "
            "border-radius: 4px; background: white;"
        )
        form.addRow(history_label, self.history_spin)

        autocomplete_label = QLabel(t("preferences.intellisense"))
        autocomplete_label.setStyleSheet("font-size: 12px; color: #434655;")
        self.autocomplete_check = QCheckBox(t("preferences.autocomplete"))
        form.addRow(autocomplete_label, self.autocomplete_check)

        section_layout.addLayout(form)
        layout.addWidget(section)

        return self._scroll(inner)

    def _page_shortcuts(self) -> QScrollArea:
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        header = self._create_section_header(t("preferences.shortcuts"))
        header.setStyleSheet(
            "font-size: 11px; font-weight: 700; letter-spacing: 0.05em; "
            "text-transform: uppercase; color: #004ac6; padding-bottom: 8px; "
            "border-bottom: 1px solid #c3c6d7;"
        )
        layout.addWidget(header)

        self.shortcut_table = QTableWidget(0, 2)
        self.shortcut_table.setHorizontalHeaderLabels(
            [t("preferences.action"), t("preferences.shortcut")]
        )
        self.shortcut_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.shortcut_table.setAlternatingRowColors(True)
        self.shortcut_table.setEditTriggers(QTableWidget.DoubleClicked)
        self.shortcut_table.setStyleSheet(
            "QTableWidget {"
            "  border: 1px solid #c3c6d7;"
            "  border-radius: 4px;"
            "  background: #ffffff;"
            "}"
            "QHeaderView::section {"
            "  background: #f8f9ff;"
            "  color: #434655;"
            "  font-size: 11px;"
            "  font-weight: 700;"
            "  letter-spacing: 0.05em;"
            "  text-transform: uppercase;"
            "}"
            "QTableWidget::item {"
            "  padding: 8px 12px;"
            "}"
            "QTableWidget::item:hover {"
            "  background: #eff4ff;"
            "}"
        )
        layout.addWidget(self.shortcut_table)

        self.btn_restore = QPushButton(t("preferences.restore_defaults"))
        self.btn_restore.setStyleSheet(
            "QPushButton {"
            "  background: transparent;"
            "  border: 1px solid #c3c6d7;"
            "  color: #0b1c30;"
            "  padding: 6px 16px;"
            "  border-radius: 4px;"
            "  font-size: 13px;"
            "}"
            "QPushButton:hover {"
            "  background: #eff4ff;"
            "}"
        )
        self.btn_restore.clicked.connect(self._restore_shortcuts)
        layout.addWidget(self.btn_restore, alignment=Qt.AlignRight)

        return self._scroll(inner)

    def _page_advanced(self) -> QScrollArea:
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        header = self._create_section_header(t("preferences.advanced"))
        header.setStyleSheet(
            "font-size: 11px; font-weight: 700; letter-spacing: 0.05em; "
            "text-transform: uppercase; color: #004ac6; padding-bottom: 8px; "
            "border-bottom: 1px solid #c3c6d7;"
        )
        layout.addWidget(header)

        self.hw_accel_check = QCheckBox(t("preferences.hardware_acceleration"))
        self.hw_accel_check.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.hw_accel_check)

        autosave_row = QHBoxLayout()
        self.lbl_autosave_pre = QLabel(t("preferences.autosave_interval"))
        self.lbl_autosave_pre.setStyleSheet("font-size: 12px; color: #434655;")
        self.autosave_spin = QSpinBox()
        self.autosave_spin.setRange(0, 60)
        self.autosave_spin.setStyleSheet(
            "min-height: 32px; padding: 0 6px; border: 1px solid #c3c6d7; "
            "border-radius: 4px; background: white; width: 80px;"
        )
        self.lbl_autosave_post = QLabel(t("preferences.autosave_minutes"))
        self.lbl_autosave_post.setStyleSheet("font-size: 12px; color: #434655;")
        autosave_row.addWidget(self.lbl_autosave_pre)
        autosave_row.addWidget(self.autosave_spin)
        autosave_row.addWidget(self.lbl_autosave_post)
        autosave_row.addStretch()
        layout.addLayout(autosave_row)

        self.lbl_restart = QLabel(t("preferences.restart_notice"))
        self.lbl_restart.setStyleSheet("color: #737686; font-size: 12px;")
        layout.addWidget(self.lbl_restart)

        layout.addStretch()

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #c3c6d7; border-style: dashed;")
        layout.addWidget(separator)

        reset_row = QHBoxLayout()
        reset_label = QLabel(t("preferences.factory_reset"))
        reset_label.setStyleSheet("font-size: 12px; color: #dc2626; font-weight: 600;")

        self.btn_reset_all = QPushButton(t("preferences.reset_all"))
        self.btn_reset_all.setStyleSheet(
            "QPushButton {"
            "  background: transparent;"
            "  border: 1px solid #fecaca;"
            "  color: #dc2626;"
            "  padding: 8px 16px;"
            "  border-radius: 4px;"
            "  font-size: 13px;"
            "}"
            "QPushButton:hover {"
            "  background: #fff0f0;"
            "}"
        )
        self.btn_reset_all.clicked.connect(self._reset_all)

        reset_row.addWidget(reset_label)
        reset_row.addStretch()
        reset_row.addWidget(self.btn_reset_all)
        layout.addLayout(reset_row)

        hint_label = QLabel(t("preferences.reset_hint"))
        hint_label.setStyleSheet("color: #737686; font-size: 10px;")
        layout.addWidget(hint_label)

        return self._scroll(inner)

    def _load_settings(self):
        s = self.settings

        idx = self.theme_combo.findData(s.get("theme", "light"))
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)

        self._set_accent(s.get("accent", "#004ac6"))

        try:
            self.ui_font_combo.setCurrentFont(QFont(s.get("ui_font", "Segoe UI")))
        except Exception:
            pass
        self.ui_font_size_spin.setValue(s.get("ui_font_size", 10))

        idx = self.bg_combo.findData(s.get("canvas_bg", "grid"))
        if idx >= 0:
            self.bg_combo.setCurrentIndex(idx)

        lang_code = get_i18n().get_language()
        idx = self.lang_combo.findData(lang_code)
        if idx >= 0:
            self.lang_combo.blockSignals(True)
            self.lang_combo.setCurrentIndex(idx)
            self.lang_combo.blockSignals(False)

        self.line_width_spin.setValue(s.get("line_width", 1.5))
        self.point_size_spin.setValue(s.get("point_size", 4))
        self.aa_check.setChecked(s.get("aa_enabled", True))
        self.speed_slider.setValue(s.get("anim_speed", 50))

        try:
            self.con_font_combo.setCurrentFont(QFont(s.get("console_font", "Consolas")))
        except Exception:
            pass
        self.con_font_size_spin.setValue(s.get("console_font_size", 11))
        self.history_spin.setValue(s.get("console_history", 1000))
        self.autocomplete_check.setChecked(s.get("autocomplete", True))

        self.hw_accel_check.setChecked(s.get("hw_accel", False))
        self.autosave_spin.setValue(s.get("autosave_interval", 5))

        shortcuts = s.get("shortcuts", {})
        self.shortcut_table.setRowCount(len(shortcuts))
        for row, (action, key) in enumerate(shortcuts.items()):
            self.shortcut_table.setItem(row, 0, QTableWidgetItem(action))
            self.shortcut_table.setItem(row, 1, QTableWidgetItem(key))

    def _set_accent(self, hex_color: str):
        self.settings["accent"] = hex_color
        for color, btn in self.accent_btns:
            selected = color == hex_color
            btn.setChecked(selected)
            border = "#1e293b" if selected else "transparent"
            btn.setStyleSheet(
                f"background-color:{color}; border-radius:13px; border:2px solid {border};"
            )

    def _on_lang_combo_changed(self, index: int):
        lang_code = self.lang_combo.itemData(index)
        if not lang_code:
            return
        if lang_code != get_i18n().get_language():
            get_i18n().set_language(lang_code)
            self.language_changed.emit(lang_code)

    def _on_lang_changed_extern(self, lang_code: str):
        self.retranslate_ui()
        idx = self.lang_combo.findData(lang_code)
        if idx >= 0 and self.lang_combo.currentIndex() != idx:
            self.lang_combo.blockSignals(True)
            self.lang_combo.setCurrentIndex(idx)
            self.lang_combo.blockSignals(False)

    def retranslate_ui(self):
        self.setWindowTitle(t("preferences.title"))

        self.tabs.setTabText(0, t("preferences.appearance"))
        self.tabs.setTabText(1, t("preferences.graphics"))
        self.tabs.setTabText(2, t("preferences.console_tab"))
        self.tabs.setTabText(3, t("preferences.shortcuts"))
        self.tabs.setTabText(4, t("preferences.advanced"))

        self.btn_cancel.setText(t("dialogs.cancel"))
        self.btn_apply.setText(t("preferences.apply"))
        self.btn_ok.setText(t("preferences.ok"))

    def _apply_settings(self):
        theme_key = self.theme_combo.currentData()
        if theme_key:
            set_theme(theme_key)
            self.settings["theme"] = theme_key
            self.theme_changed.emit(theme_key)

        self.accent_color_changed.emit(self.settings["accent"])

        family = self.ui_font_combo.currentFont().family()
        size   = self.ui_font_size_spin.value()
        self.settings.update({"ui_font": family, "ui_font_size": size})
        self.font_changed.emit(family, size)

        lang_code = self.lang_combo.currentData()
        if lang_code:
            self.settings["language"] = lang_code
            self.language_changed.emit(lang_code)

        gfx = {
            "line_width": self.line_width_spin.value(),
            "point_size": self.point_size_spin.value(),
            "aa":         self.aa_check.isChecked(),
            "speed":      self.speed_slider.value(),
        }
        self.settings.update({
            "line_width": gfx["line_width"],
            "point_size": gfx["point_size"],
            "aa_enabled": gfx["aa"],
            "anim_speed": gfx["speed"],
        })
        self.graphics_settings_changed.emit(gfx)

        con = {
            "font":         self.con_font_combo.currentFont().family(),
            "font_size":    self.con_font_size_spin.value(),
            "history":      self.history_spin.value(),
            "autocomplete": self.autocomplete_check.isChecked(),
        }
        self.settings.update({
            "console_font":      con["font"],
            "console_font_size": con["font_size"],
            "console_history":   con["history"],
            "autocomplete":      con["autocomplete"],
        })
        self.console_settings_changed.emit(con)

        adv = {
            "hw_accel":  self.hw_accel_check.isChecked(),
            "autosave":  self.autosave_spin.value(),
        }
        self.settings.update({
            "hw_accel":          adv["hw_accel"],
            "autosave_interval": adv["autosave"],
        })
        self.advanced_settings_changed.emit(adv)

        shortcuts = {}
        for row in range(self.shortcut_table.rowCount()):
            action_item = self.shortcut_table.item(row, 0)
            key_item    = self.shortcut_table.item(row, 1)
            if action_item and key_item:
                shortcuts[action_item.text()] = key_item.text()
        self.settings["shortcuts"] = shortcuts
        self.shortcuts_changed.emit(shortcuts)

    def _on_ok(self):
        self._apply_settings()
        self.accept()

    def _restore_shortcuts(self):
        defaults = self._default_settings()["shortcuts"]
        self.settings["shortcuts"] = defaults
        self.shortcut_table.setRowCount(len(defaults))
        for row, (action, key) in enumerate(defaults.items()):
            self.shortcut_table.setItem(row, 0, QTableWidgetItem(action))
            self.shortcut_table.setItem(row, 1, QTableWidgetItem(key))

    def _reset_all(self):
        result = QMessageBox.question(
            self,
            t("preferences.title"),
            t("preferences.reset_confirm"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result == QMessageBox.Yes:
            self.settings = self._default_settings()
            self._load_settings()

    def closeEvent(self, event):
        get_i18n().remove_language_change_listener(self._on_lang_changed_extern)
        super().closeEvent(event)