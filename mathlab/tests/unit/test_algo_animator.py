"""Tests for the AlgoAnimator step-through animation engine.

Covers algorithm loading, single-step advancement, and reset behavior.
Extracted from the legacy ``test_core.py`` module.
"""
import pytest


class TestAlgoAnimator:
    """Tests for the AlgoAnimator visualization engine."""

    @pytest.mark.unit
    def test_load_algorithm(self, animator):
        result = animator.load_algorithm('bubble_sort', arr=[5, 3, 8, 1])
        assert result
        assert animator.current_algorithm == 'bubble_sort'

    @pytest.mark.unit
    def test_step(self, animator):
        animator.load_algorithm('bubble_sort', arr=[5, 3, 8, 1])
        state = animator.step()
        assert state is not None
        assert state['type'] == 'sorting'

    @pytest.mark.unit
    def test_reset(self, animator):
        animator.load_algorithm('bubble_sort', arr=[5, 3, 8, 1])
        animator.step()
        animator.reset()
        assert animator.current_state is None
