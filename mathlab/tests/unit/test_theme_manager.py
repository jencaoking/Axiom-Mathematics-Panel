"""Unit tests for mathlab.utils.theme_manager.

Extracted from test_utils.py (TestThemeManager). Covers THEMES
registry validation and get_theme_colors retrieval for light, dark,
and sepia themes.
"""

import pytest

from mathlab.utils.theme_manager import THEMES, get_theme_colors


class TestThemeManager:
    """Tests for the theme manager module."""

    @pytest.mark.unit
    def test_themes_exist(self):
        assert 'light' in THEMES
        assert 'dark' in THEMES
        assert 'sepia' in THEMES

    @pytest.mark.unit
    def test_theme_has_required_keys(self):
        for theme_id, theme in THEMES.items():
            assert 'name' in theme
            assert 'background' in theme
            assert 'foreground' in theme
            assert 'accent' in theme

    @pytest.mark.unit
    def test_get_theme_colors(self):
        colors = get_theme_colors('light')
        assert colors['name'] == 'Light'
        assert colors['background'] == '#ffffff'

    @pytest.mark.unit
    def test_get_theme_colors_default(self):
        colors = get_theme_colors()
        assert colors is not None

    @pytest.mark.unit
    def test_dark_theme_colors(self):
        colors = get_theme_colors('dark')
        assert colors['background'] == '#1e1e1e'
        assert colors['foreground'] == '#d4d4d4'

    @pytest.mark.unit
    def test_sepia_theme_colors(self):
        colors = get_theme_colors('sepia')
        assert colors['background'] == '#f4ecd8'
