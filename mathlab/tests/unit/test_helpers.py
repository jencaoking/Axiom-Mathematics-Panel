"""Unit tests for mathlab.utils.helpers utility functions.

Merged and deduplicated from test_core.py (TestHelpers) and
test_utils.py (TestHelpersUtils). Covers lerp, clamp, distance,
midpoint, parse_coordinates, generate_id, and format_number.
"""

import pytest

from mathlab.utils.helpers import (
    lerp,
    clamp,
    distance,
    midpoint,
    parse_coordinates,
    generate_id,
    format_number,
)


class TestHelpers:
    """Tests for the helper utility functions."""

    @pytest.mark.unit
    def test_lerp_exact_middle(self):
        assert lerp(0, 100, 0.5) == pytest.approx(50)

    @pytest.mark.unit
    def test_lerp_quarter(self):
        assert lerp(0, 100, 0.25) == pytest.approx(25)

    @pytest.mark.unit
    def test_lerp_at_start(self):
        assert lerp(0, 100, 0) == 0

    @pytest.mark.unit
    def test_lerp_at_end(self):
        assert lerp(0, 100, 1) == 100

    @pytest.mark.unit
    def test_clamp_within_range(self):
        assert clamp(50, 0, 100) == 50

    @pytest.mark.unit
    def test_clamp_above_range(self):
        assert clamp(150, 0, 100) == 100

    @pytest.mark.unit
    def test_clamp_below_range(self):
        assert clamp(-50, 0, 100) == 0

    @pytest.mark.unit
    def test_distance_horizontal(self):
        assert distance((0, 0), (3, 0)) == pytest.approx(3.0)

    @pytest.mark.unit
    def test_distance_vertical(self):
        assert distance((0, 0), (0, 4)) == pytest.approx(4.0)

    @pytest.mark.unit
    def test_distance_diagonal(self):
        d = distance((0, 0), (3, 4))
        assert d == pytest.approx(5.0, abs=1e-1)

    @pytest.mark.unit
    def test_midpoint_origin_to_one(self):
        result = midpoint((0, 0), (2, 2))
        assert result == (1.0, 1.0)

    @pytest.mark.unit
    def test_midpoint_negative(self):
        result = midpoint((-1, -1), (1, 1))
        assert result == (0.0, 0.0)

    @pytest.mark.unit
    def test_parse_coordinates_simple(self):
        result = parse_coordinates("(1, 2)")
        assert result == (1.0, 2.0)

    @pytest.mark.unit
    def test_parse_coordinates_float(self):
        result = parse_coordinates("(1.5, 2.7)")
        assert result == (1.5, 2.7)

    @pytest.mark.unit
    def test_parse_coordinates_no_parens(self):
        result = parse_coordinates("1, 2")
        assert result == (1.0, 2.0)

    @pytest.mark.unit
    def test_generate_id_prefix(self):
        id1 = generate_id("point")
        assert id1.startswith("point_")

    @pytest.mark.unit
    def test_generate_id_unique(self):
        id1 = generate_id("test")
        id2 = generate_id("test")
        assert id1 != id2

    @pytest.mark.unit
    def test_format_number_default_decimals(self):
        result = format_number(3.14159)
        assert result == "3.14"

    @pytest.mark.unit
    def test_format_number_custom_decimals(self):
        result = format_number(3.14159, decimals=4)
        assert result == "3.1416"
