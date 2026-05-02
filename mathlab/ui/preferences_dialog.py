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


# ---------------------------------------------------------------------------
# Sidebar stylesheet
# ---------------------------------------------------------------------------
_TAB_STYLE = """
QTabWidget::pane {
    border: none;
    border-left: 1px solid #c3c6d7;
    background: white;
}
QTabBar {
    background: #f8f9ff;
}
QTabBar::tab {
    padding: 12px 20px;
    text-align: left;
    min-width: 140px;
    font-size: 13px;
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
    background: #eef1ff;
}
"""

_ACCENT_COLORS = [
    "#004ac6",  # MathLab blue (default)
    "#10B981",  # emerald
    "#8B5CF6",  # violet
    "#F59E0B",  # amber
    "#EF4444",  # red
]


# ---------------------------------------------------------------------------
class PreferencesDialog(QDialog):
    """Full-featured preferences / settings dialog for MathLab."""

    # ── signals ──────────────────────────────────────────────────────────
    theme_changed = Signal(str)
    accent_color_changed = Signal(str)
    font_changed = Signal(str, int)
    language_changed = Signal(str)
    graphics_settings_changed = Signal(dict)
    console_settings_changed = Signal(dict)
    shortcuts_changed = Signal(dict)
    advanced_settings_changed = Signal(dict)

    # ── construction ─────────────────────────────────────────────────────
    def __init__(self, parent=None, initial_settings: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle(t("preferences.title"))
        self.setMinimumSize(700, 500)
        self.resize(780, 540)

        self.settings: dict = initial_settings or self._default_settings()

        self._build_ui()
        self._load_settings()

        # Subscribe to external language changes (e.g. triggered from menu)
        get_i18n().add_language_change_listener(self._on_lang_changed_extern)

    # ── default settings ─────────────────────────────────────────────────
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

    # ── UI assembly ───────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── sidebar tab widget ──
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.setStyleSheet(_TAB_STYLE)

        self.tabs.addTab(self._page_appearance(), t("preferences.appearance"))
        self.tabs.addTab(self._page_graphics(),   t("preferences.graphics"))
        self.tabs.addTab(self._page_console(),    t("preferences.console_tab"))
        self.tabs.addTab(self._page_shortcuts(),  t("preferences.shortcuts"))
        self.tabs.addTab(self._page_advanced(),   t("preferences.advanced"))

        root.addWidget(self.tabs, 1)

        # ── bottom button bar ──
        bar = QWidget()
        bar.setStyleSheet(
            "background: #f5f6fc; border-top: 1px solid #c3c6d7;"
        )
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(16, 8, 16, 8)
        bar_layout.setSpacing(8)

        self.btn_cancel = QPushButton(t("dialogs.cancel"))
        self.btn_apply  = QPushButton(t("preferences.apply"))
        self.btn_ok     = QPushButton(t("preferences.ok"))
        self.btn_ok.setDefault(True)
        self.btn_ok.setStyleSheet(
            "QPushButton {"
            "  font-weight: 600;"
            "  background: #004ac6;"
            "  color: white;"
            "  padding: 6px 24px;"
            "  border-radius: 4px;"
            "}"
            "QPushButton:hover { background: #0057e7; }"
            "QPushButton:pressed { background: #003a9e; }"
        )

        bar_layout.addStretch()
        bar_layout.addWidget(self.btn_cancel)
        bar_layout.addWidget(self.btn_apply)
        bar_layout.addWidget(self.btn_ok)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_apply.clicked.connect(self._apply_settings)
        self.btn_ok.clicked.connect(self._on_ok)

        root.addWidget(bar)

    # ── helper: wrap inner widget in a scroll area ──
    @staticmethod
    def _scroll(inner: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(inner)
        return scroll

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 1 — Appearance
    # ─────────────────────────────────────────────────────────────────────
    def _page_appearance(self) -> QScrollArea:
        inner = QWidget()
        form = QFormLayout(inner)
        form.setContentsMargins(30, 30, 30, 30)
        form.setSpacing(16)

        # Theme ──────────────────────────────────────────────────
        self.theme_combo = QComboBox()
        for key, data in THEMES.items():
            self.theme_combo.addItem(data["name"], key)
        self.lbl_theme = QLabel(t("preferences.theme"))
        form.addRow(self.lbl_theme, self.theme_combo)

        # Accent colour swatches ─────────────────────────────────
        accent_row = QHBoxLayout()
        accent_row.setSpacing(8)
        self.accent_btns: list[tuple[str, QPushButton]] = []
        for color in _ACCENT_COLORS:
            btn = QPushButton()
            btn.setFixedSize(26, 26)
            btn.setCheckable(True)
            btn.setStyleSheet(
                f"background-color:{color}; border-radius:13px;"
                " border:2px solid transparent;"
            )
            btn.clicked.connect(lambda _checked, c=color: self._set_accent(c))
            accent_row.addWidget(btn)
            self.accent_btns.append((color, btn))
        accent_row.addStretch()
        self.lbl_accent = QLabel(t("preferences.accent_color"))
        form.addRow(self.lbl_accent, accent_row)

        # Interface font ─────────────────────────────────────────
        self.ui_font_combo = QFontComboBox()
        self.ui_font_size_spin = QSpinBox()
        self.ui_font_size_spin.setRange(8, 24)
        self.ui_font_size_spin.setSuffix(" pt")
        font_row = QHBoxLayout()
        font_row.addWidget(self.ui_font_combo, 1)
        font_row.addWidget(self.ui_font_size_spin)
        self.lbl_font = QLabel(t("preferences.interface_font"))
        form.addRow(self.lbl_font, font_row)

        # Canvas background ──────────────────────────────────────
        self.bg_combo = QComboBox()
        self.bg_combo.addItem(t("preferences.canvas_bg_grid"),  "grid")
        self.bg_combo.addItem(t("preferences.canvas_bg_blank"), "blank")
        self.bg_combo.addItem(t("preferences.canvas_bg_polar"), "polar")
        self.lbl_bg = QLabel(t("preferences.canvas_background"))
        form.addRow(self.lbl_bg, self.bg_combo)

        # Language ───────────────────────────────────────────────
        self.lang_combo = QComboBox()
        for code, display in SUPPORTED_LANGUAGES.items():
            self.lang_combo.addItem(display, code)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_combo_changed)
        self.lbl_lang = QLabel(t("preferences.language"))
        form.addRow(self.lbl_lang, self.lang_combo)

        return self._scroll(inner)

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 2 — Graphics
    # ─────────────────────────────────────────────────────────────────────
    def _page_graphics(self) -> QScrollArea:
        inner = QWidget()
        form = QFormLayout(inner)
        form.setContentsMargins(30, 30, 30, 30)
        form.setSpacing(16)

        self.line_width_spin = QDoubleSpinBox()
        self.line_width_spin.setRange(0.1, 10.0)
        self.line_width_spin.setSingleStep(0.1)
        self.line_width_spin.setSuffix(" px")
        self.lbl_line_width = QLabel(t("preferences.default_line_width"))
        form.addRow(self.lbl_line_width, self.line_width_spin)

        self.point_size_spin = QSpinBox()
        self.point_size_spin.setRange(1, 20)
        self.point_size_spin.setSuffix(" px")
        self.lbl_point_size = QLabel(t("preferences.default_point_size"))
        form.addRow(self.lbl_point_size, self.point_size_spin)

        self.aa_check = QCheckBox(t("preferences.antialiasing"))
        self.lbl_rendering = QLabel(t("preferences.rendering"))
        form.addRow(self.lbl_rendering, self.aa_check)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(10, 200)
        self.lbl_anim_speed = QLabel(t("preferences.animation_speed"))
        form.addRow(self.lbl_anim_speed, self.speed_slider)

        return self._scroll(inner)

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 3 — Console
    # ─────────────────────────────────────────────────────────────────────
    def _page_console(self) -> QScrollArea:
        inner = QWidget()
        form = QFormLayout(inner)
        form.setContentsMargins(30, 30, 30, 30)
        form.setSpacing(16)

        self.con_font_combo = QFontComboBox()
        self.con_font_size_spin = QSpinBox()
        self.con_font_size_spin.setRange(8, 30)
        self.con_font_size_spin.setSuffix(" pt")
        cfont_row = QHBoxLayout()
        cfont_row.addWidget(self.con_font_combo, 1)
        cfont_row.addWidget(self.con_font_size_spin)
        self.lbl_con_font = QLabel(t("preferences.console_font"))
        form.addRow(self.lbl_con_font, cfont_row)

        self.history_spin = QSpinBox()
        self.history_spin.setRange(100, 10000)
        self.history_spin.setSingleStep(100)
        self.lbl_history = QLabel(t("preferences.history_limit"))
        form.addRow(self.lbl_history, self.history_spin)

        self.autocomplete_check = QCheckBox(t("preferences.autocomplete"))
        self.lbl_intellisense = QLabel(t("preferences.intellisense"))
        form.addRow(self.lbl_intellisense, self.autocomplete_check)

        return self._scroll(inner)

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 4 — Shortcuts
    # ─────────────────────────────────────────────────────────────────────
    def _page_shortcuts(self) -> QScrollArea:
        inner = QWidget()
        vbox = QVBoxLayout(inner)
        vbox.setContentsMargins(20, 20, 20, 20)
        vbox.setSpacing(12)

        self.shortcut_table = QTableWidget(0, 2)
        self.shortcut_table.setHorizontalHeaderLabels(
            [t("preferences.action"), t("preferences.shortcut")]
        )
        self.shortcut_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.shortcut_table.setAlternatingRowColors(True)
        self.shortcut_table.setEditTriggers(QTableWidget.DoubleClicked)
        vbox.addWidget(self.shortcut_table)

        self.btn_restore = QPushButton(t("preferences.restore_defaults"))
        self.btn_restore.clicked.connect(self._restore_shortcuts)
        vbox.addWidget(self.btn_restore, alignment=Qt.AlignRight)

        return self._scroll(inner)

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 5 — Advanced
    # ─────────────────────────────────────────────────────────────────────
    def _page_advanced(self) -> QScrollArea:
        inner = QWidget()
        vbox = QVBoxLayout(inner)
        vbox.setContentsMargins(30, 30, 30, 30)
        vbox.setSpacing(16)

        self.hw_accel_check = QCheckBox("Enable Hardware Acceleration (OpenGL)")
        vbox.addWidget(self.hw_accel_check)

        autosave_row = QHBoxLayout()
        self.lbl_autosave_pre  = QLabel("Auto-save interval:")
        self.autosave_spin = QSpinBox()
        self.autosave_spin.setRange(0, 60)
        self.lbl_autosave_post = QLabel("minutes  (0 = disabled)")
        autosave_row.addWidget(self.lbl_autosave_pre)
        autosave_row.addWidget(self.autosave_spin)
        autosave_row.addWidget(self.lbl_autosave_post)
        autosave_row.addStretch()
        vbox.addLayout(autosave_row)

        # Restart notice
        self.lbl_restart = QLabel(t("preferences.restart_notice"))
        self.lbl_restart.setStyleSheet("color:#737686; font-size:12px;")
        vbox.addWidget(self.lbl_restart)

        vbox.addStretch()

        # Destructive reset button
        self.btn_reset_all = QPushButton(t("preferences.reset_all"))
        self.btn_reset_all.setStyleSheet(
            "QPushButton {"
            "  color: #dc2626;"
            "  border: 1px solid #fecaca;"
            "  padding: 8px 16px;"
            "  border-radius: 4px;"
            "}"
            "QPushButton:hover { background: #fff0f0; }"
        )
        self.btn_reset_all.clicked.connect(self._reset_all)
        vbox.addWidget(self.btn_reset_all)

        return self._scroll(inner)

    # ─────────────────────────────────────────────────────────────────────
    # Settings load / save
    # ─────────────────────────────────────────────────────────────────────
    def _load_settings(self):
        """Populate all controls from *self.settings*."""
        s = self.settings

        # Appearance ─────────────────────────────────────────────
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

        # Graphics ───────────────────────────────────────────────
        self.line_width_spin.setValue(s.get("line_width", 1.5))
        self.point_size_spin.setValue(s.get("point_size", 4))
        self.aa_check.setChecked(s.get("aa_enabled", True))
        self.speed_slider.setValue(s.get("anim_speed", 50))

        # Console ────────────────────────────────────────────────
        try:
            self.con_font_combo.setCurrentFont(
                QFont(s.get("console_font", "Consolas"))
            )
        except Exception:
            pass
        self.con_font_size_spin.setValue(s.get("console_font_size", 11))
        self.history_spin.setValue(s.get("console_history", 1000))
        self.autocomplete_check.setChecked(s.get("autocomplete", True))

        # Advanced ───────────────────────────────────────────────
        self.hw_accel_check.setChecked(s.get("hw_accel", False))
        self.autosave_spin.setValue(s.get("autosave_interval", 5))

        # Shortcuts ──────────────────────────────────────────────
        shortcuts = s.get("shortcuts", {})
        self.shortcut_table.setRowCount(len(shortcuts))
        for row, (action, key) in enumerate(shortcuts.items()):
            self.shortcut_table.setItem(row, 0, QTableWidgetItem(action))
            self.shortcut_table.setItem(row, 1, QTableWidgetItem(key))

    # ─────────────────────────────────────────────────────────────────────
    # Accent helper
    # ─────────────────────────────────────────────────────────────────────
    def _set_accent(self, hex_color: str):
        self.settings["accent"] = hex_color
        for color, btn in self.accent_btns:
            selected = color == hex_color
            btn.setChecked(selected)
            border = "#1e293b" if selected else "transparent"
            btn.setStyleSheet(
                f"background-color:{color}; border-radius:13px;"
                f" border:2px solid {border};"
            )

    # ─────────────────────────────────────────────────────────────────────
    # Language handling
    # ─────────────────────────────────────────────────────────────────────
    def _on_lang_combo_changed(self, index: int):
        lang_code = self.lang_combo.itemData(index)
        if not lang_code:
            return
        if lang_code != get_i18n().get_language():
            get_i18n().set_language(lang_code)  # triggers _on_lang_changed_extern
            self.language_changed.emit(lang_code)

    def _on_lang_changed_extern(self, lang_code: str):
        """Called by i18n manager when language changes from *any* source."""
        self.retranslate_ui()
        # Keep the combo in sync without triggering another change
        idx = self.lang_combo.findData(lang_code)
        if idx >= 0 and self.lang_combo.currentIndex() != idx:
            self.lang_combo.blockSignals(True)
            self.lang_combo.setCurrentIndex(idx)
            self.lang_combo.blockSignals(False)

    # ─────────────────────────────────────────────────────────────────────
    # retranslate_ui — refresh all visible strings
    # ─────────────────────────────────────────────────────────────────────
    def retranslate_ui(self):
        self.setWindowTitle(t("preferences.title"))

        # Tab labels
        self.tabs.setTabText(0, t("preferences.appearance"))
        self.tabs.setTabText(1, t("preferences.graphics"))
        self.tabs.setTabText(2, t("preferences.console_tab"))
        self.tabs.setTabText(3, t("preferences.shortcuts"))
        self.tabs.setTabText(4, t("preferences.advanced"))

        # Bottom buttons
        self.btn_cancel.setText(t("dialogs.cancel"))
        self.btn_apply.setText(t("preferences.apply"))
        self.btn_ok.setText(t("preferences.ok"))

        # ── Appearance page ──────────────────────────────────────
        self.lbl_theme.setText(t("preferences.theme"))
        self.lbl_accent.setText(t("preferences.accent_color"))
        self.lbl_font.setText(t("preferences.interface_font"))
        self.lbl_bg.setText(t("preferences.canvas_background"))
        self.lbl_lang.setText(t("preferences.language"))

        # Refresh bg_combo item texts (data keys stay the same)
        self.bg_combo.setItemText(0, t("preferences.canvas_bg_grid"))
        self.bg_combo.setItemText(1, t("preferences.canvas_bg_blank"))
        self.bg_combo.setItemText(2, t("preferences.canvas_bg_polar"))

        # ── Graphics page ────────────────────────────────────────
        self.lbl_line_width.setText(t("preferences.default_line_width"))
        self.lbl_point_size.setText(t("preferences.default_point_size"))
        self.aa_check.setText(t("preferences.antialiasing"))
        self.lbl_rendering.setText(t("preferences.rendering"))
        self.lbl_anim_speed.setText(t("preferences.animation_speed"))

        # ── Console page ─────────────────────────────────────────
        self.lbl_con_font.setText(t("preferences.console_font"))
        self.lbl_history.setText(t("preferences.history_limit"))
        self.autocomplete_check.setText(t("preferences.autocomplete"))
        self.lbl_intellisense.setText(t("preferences.intellisense"))

        # ── Shortcuts page ───────────────────────────────────────
        self.shortcut_table.setHorizontalHeaderLabels(
            [t("preferences.action"), t("preferences.shortcut")]
        )
        self.btn_restore.setText(t("preferences.restore_defaults"))

        # ── Advanced page ────────────────────────────────────────
        self.lbl_restart.setText(t("preferences.restart_notice"))
        self.btn_reset_all.setText(t("preferences.reset_all"))

    # ─────────────────────────────────────────────────────────────────────
    # Apply / OK / Cancel
    # ─────────────────────────────────────────────────────────────────────
    def _apply_settings(self):
        """Collect UI state and emit all change signals."""
        # Theme
        theme_key = self.theme_combo.currentData()
        if theme_key:
            set_theme(theme_key)
            self.settings["theme"] = theme_key
            self.theme_changed.emit(theme_key)

        # Accent
        self.accent_color_changed.emit(self.settings["accent"])

        # Font
        family = self.ui_font_combo.currentFont().family()
        size   = self.ui_font_size_spin.value()
        self.settings.update({"ui_font": family, "ui_font_size": size})
        self.font_changed.emit(family, size)

        # Language
        lang_code = self.lang_combo.currentData()
        if lang_code:
            self.settings["language"] = lang_code
            self.language_changed.emit(lang_code)

        # Graphics
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

        # Console
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

        # Advanced
        adv = {
            "hw_accel":  self.hw_accel_check.isChecked(),
            "autosave":  self.autosave_spin.value(),
        }
        self.settings.update({
            "hw_accel":          adv["hw_accel"],
            "autosave_interval": adv["autosave"],
        })
        self.advanced_settings_changed.emit(adv)

        # Shortcuts
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

    # ─────────────────────────────────────────────────────────────────────
    # Shortcut / full reset
    # ─────────────────────────────────────────────────────────────────────
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
            "Are you sure you want to restore ALL settings to factory defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result == QMessageBox.Yes:
            self.settings = self._default_settings()
            self._load_settings()

    # ─────────────────────────────────────────────────────────────────────
    # Clean-up
    # ─────────────────────────────────────────────────────────────────────
    def closeEvent(self, event):
        get_i18n().remove_language_change_listener(self._on_lang_changed_extern)
        super().closeEvent(event)
