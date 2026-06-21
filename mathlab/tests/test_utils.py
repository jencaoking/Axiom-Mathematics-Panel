import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mathlab.utils.theme_manager import THEMES, get_theme_colors, get_current_theme


class TestThemeManager(unittest.TestCase):
    def test_themes_exist(self):
        self.assertIn('light', THEMES)
        self.assertIn('dark', THEMES)
        self.assertIn('sepia', THEMES)

    def test_theme_has_required_keys(self):
        for theme_id, theme in THEMES.items():
            self.assertIn('name', theme)
            self.assertIn('background', theme)
            self.assertIn('foreground', theme)
            self.assertIn('accent', theme)

    def test_get_theme_colors(self):
        colors = get_theme_colors('light')
        self.assertEqual(colors['name'], 'Light')
        self.assertEqual(colors['background'], '#ffffff')

    def test_get_theme_colors_default(self):
        colors = get_theme_colors()
        self.assertIsNotNone(colors)

    def test_dark_theme_colors(self):
        colors = get_theme_colors('dark')
        self.assertEqual(colors['background'], '#1e1e1e')
        self.assertEqual(colors['foreground'], '#d4d4d4')

    def test_sepia_theme_colors(self):
        colors = get_theme_colors('sepia')
        self.assertEqual(colors['background'], '#f4ecd8')


class TestLatexRendererUtils(unittest.TestCase):
    def test_export_empty_canvas(self):
        from mathlab.utils.latex_renderer import export_canvas_to_latex
        latex = export_canvas_to_latex([])
        self.assertIn(r'\documentclass', latex)
        self.assertIn(r'\begin{tikzpicture}', latex)

    def test_export_point(self):
        from mathlab.utils.latex_renderer import export_canvas_to_latex
        objects = [{'type': 'Point', 'name': 'A', 'coordinates': {'x': 1, 'y': 2}}]
        latex = export_canvas_to_latex(objects)
        self.assertIn(r'\fill[blue]', latex)
        self.assertIn('A', latex)

    def test_export_segment(self):
        from mathlab.utils.latex_renderer import export_canvas_to_latex
        objects = [{'type': 'Segment', 'name': 'AB', 'coordinates': {'x1': 0, 'y1': 0, 'x2': 3, 'y2': 4}}]
        latex = export_canvas_to_latex(objects)
        self.assertIn(r'\draw[thick, blue]', latex)

    def test_export_circle(self):
        from mathlab.utils.latex_renderer import export_canvas_to_latex
        objects = [{'type': 'Circle', 'name': 'C', 'coordinates': {'cx': 0, 'cy': 0, 'r': 5}}]
        latex = export_canvas_to_latex(objects)
        self.assertIn(r'\draw[thick, teal]', latex)
        self.assertIn('circle', latex)

    def test_export_polygon(self):
        from mathlab.utils.latex_renderer import export_canvas_to_latex
        objects = [{'type': 'Polygon', 'name': 'P', 'coordinates': {'points': [[0, 0], [1, 0], [0.5, 1]]}}]
        latex = export_canvas_to_latex(objects)
        self.assertIn(r'\draw[thick, purple', latex)

    def test_format_point(self):
        from mathlab.utils.latex_renderer import format_point
        result = format_point('A', 1.5, 2.5)
        self.assertIn('A', result)
        self.assertIn('1.5', result)

    def test_format_segment(self):
        from mathlab.utils.latex_renderer import format_segment
        result = format_segment('AB', 'A', 'B')
        self.assertIn(r'\overline', result)

    def test_format_circle(self):
        from mathlab.utils.latex_renderer import format_circle
        result = format_circle('C', 'O', 5)
        self.assertIn('C', result)

    def test_format_polygon(self):
        from mathlab.utils.latex_renderer import format_polygon
        result = format_polygon('P', ['A', 'B', 'C'])
        self.assertIn('P', result)


class TestHelpersUtils(unittest.TestCase):
    def test_lerp_exact_middle(self):
        from mathlab.utils.helpers import lerp
        self.assertAlmostEqual(lerp(0, 100, 0.5), 50)

    def test_lerp_quarter(self):
        from mathlab.utils.helpers import lerp
        self.assertAlmostEqual(lerp(0, 100, 0.25), 25)

    def test_lerp_at_start(self):
        from mathlab.utils.helpers import lerp
        self.assertEqual(lerp(0, 100, 0), 0)

    def test_lerp_at_end(self):
        from mathlab.utils.helpers import lerp
        self.assertEqual(lerp(0, 100, 1), 100)

    def test_clamp_within_range(self):
        from mathlab.utils.helpers import clamp
        self.assertEqual(clamp(50, 0, 100), 50)

    def test_clamp_above_range(self):
        from mathlab.utils.helpers import clamp
        self.assertEqual(clamp(150, 0, 100), 100)

    def test_clamp_below_range(self):
        from mathlab.utils.helpers import clamp
        self.assertEqual(clamp(-50, 0, 100), 0)

    def test_distance_horizontal(self):
        from mathlab.utils.helpers import distance
        self.assertAlmostEqual(distance((0, 0), (3, 0)), 3.0)

    def test_distance_vertical(self):
        from mathlab.utils.helpers import distance
        self.assertAlmostEqual(distance((0, 0), (0, 4)), 4.0)

    def test_distance_diagonal(self):
        from mathlab.utils.helpers import distance
        d = distance((0, 0), (3, 4))
        self.assertAlmostEqual(d, 5.0, places=1)

    def test_midpoint_origin_to_one(self):
        from mathlab.utils.helpers import midpoint
        result = midpoint((0, 0), (2, 2))
        self.assertEqual(result, (1.0, 1.0))

    def test_midpoint_negative(self):
        from mathlab.utils.helpers import midpoint
        result = midpoint((-1, -1), (1, 1))
        self.assertEqual(result, (0.0, 0.0))

    def test_parse_coordinates_simple(self):
        from mathlab.utils.helpers import parse_coordinates
        result = parse_coordinates('(1, 2)')
        self.assertEqual(result, (1.0, 2.0))

    def test_parse_coordinates_float(self):
        from mathlab.utils.helpers import parse_coordinates
        result = parse_coordinates('(1.5, 2.7)')
        self.assertEqual(result, (1.5, 2.7))

    def test_parse_coordinates_no_parens(self):
        from mathlab.utils.helpers import parse_coordinates
        result = parse_coordinates('1, 2')
        self.assertEqual(result, (1.0, 2.0))

    def test_generate_id_prefix(self):
        from mathlab.utils.helpers import generate_id
        id1 = generate_id('point')
        self.assertTrue(id1.startswith('point_'))

    def test_generate_id_unique(self):
        from mathlab.utils.helpers import generate_id
        id1 = generate_id('test')
        id2 = generate_id('test')
        self.assertNotEqual(id1, id2)

    def test_format_number_default_decimals(self):
        from mathlab.utils.helpers import format_number
        result = format_number(3.14159)
        self.assertEqual(result, '3.14')

    def test_format_number_custom_decimals(self):
        from mathlab.utils.helpers import format_number
        result = format_number(3.14159, decimals=4)
        self.assertEqual(result, '3.1416')


if __name__ == '__main__':
    unittest.main()