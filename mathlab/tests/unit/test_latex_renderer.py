"""Unit tests for mathlab.utils.latex_renderer.

Merged and deduplicated from test_core.py (TestLatexRenderer) and
test_utils.py (TestLatexRendererUtils). Covers export_canvas_to_latex
for point/segment/circle/polygon objects plus the format_point,
format_segment, format_circle, and format_polygon helpers.
"""

import pytest

from mathlab.utils.latex_renderer import (
    export_canvas_to_latex,
    format_point,
    format_segment,
    format_circle,
    format_polygon,
)


class TestLatexRenderer:
    """Tests for the LaTeX renderer utility functions."""

    @pytest.mark.unit
    def test_export_empty_canvas(self):
        latex = export_canvas_to_latex([])
        assert r'\documentclass' in latex
        assert r'\begin{tikzpicture}' in latex

    @pytest.mark.unit
    def test_export_point(self):
        objects = [{'type': 'Point', 'name': 'A', 'coordinates': {'x': 1, 'y': 2}}]
        latex = export_canvas_to_latex(objects)
        assert r'\fill[blue]' in latex
        assert 'A' in latex

    @pytest.mark.unit
    def test_export_segment(self):
        objects = [{'type': 'Segment', 'name': 'AB', 'coordinates': {'x1': 0, 'y1': 0, 'x2': 3, 'y2': 4}}]
        latex = export_canvas_to_latex(objects)
        assert r'\draw[thick, blue]' in latex

    @pytest.mark.unit
    def test_export_circle(self):
        objects = [{'type': 'Circle', 'name': 'C', 'coordinates': {'cx': 0, 'cy': 0, 'r': 5}}]
        latex = export_canvas_to_latex(objects)
        assert r'\draw[thick, teal]' in latex
        assert 'circle' in latex

    @pytest.mark.unit
    def test_export_polygon(self):
        objects = [{'type': 'Polygon', 'name': 'P', 'coordinates': {'points': [[0, 0], [1, 0], [0.5, 1]]}}]
        latex = export_canvas_to_latex(objects)
        assert r'\draw[thick, purple' in latex

    @pytest.mark.unit
    def test_export_canvas_to_latex(self):
        objects = [
            {'type': 'Point', 'name': 'A', 'coordinates': {'x': 1.0, 'y': 2.0}},
            {'type': 'Circle', 'name': 'C', 'coordinates': {'cx': 0.0, 'cy': 0.0, 'r': 5.0}}
        ]
        latex = export_canvas_to_latex(objects)
        assert r'\documentclass' in latex
        assert r'\draw' in latex or r'\fill' in latex

    @pytest.mark.unit
    def test_format_point(self):
        result = format_point('A', 1.5, 2.5)
        assert 'A' in result
        assert '1.5' in result

    @pytest.mark.unit
    def test_format_segment(self):
        result = format_segment('AB', 'A', 'B')
        assert r'\overline' in result

    @pytest.mark.unit
    def test_format_circle(self):
        result = format_circle('C', 'O', 5)
        assert 'C' in result

    @pytest.mark.unit
    def test_format_polygon(self):
        result = format_polygon('P', ['A', 'B', 'C'])
        assert 'P' in result
