"""Tests for the CASProvider computer-algebra facade.

Covers expression parsing, simplification, equation solving, calculus
operations (differentiation, integration), and limit evaluation.
Extracted from the legacy ``test_core.py`` module.
"""
import pytest


class TestCASProvider:
    """Tests for the CASProvider computer-algebra operations."""

    @pytest.mark.unit
    def test_parse_expression(self, cas):
        result = cas.parse_expression('x + 2')
        assert result is not None

    @pytest.mark.unit
    def test_simplify(self, cas):
        result = cas.simplify('x**2 + 2*x**2')
        assert result['success']
        assert 'x' in result['result']

    @pytest.mark.unit
    def test_solve_equation(self, cas):
        result = cas.solve_equation('x**2 - 4 = 0', 'x')
        assert result['success']

    @pytest.mark.unit
    def test_differentiate(self, cas):
        result = cas.differentiate('x**2 + 3*x', 'x')
        assert result['success']

    @pytest.mark.unit
    def test_integrate(self, cas):
        result = cas.integrate('2*x', 'x')
        assert result['success']

    @pytest.mark.unit
    def test_limit(self, cas):
        result = cas.limit('1/x', 'x', 0)
        assert result['success']
