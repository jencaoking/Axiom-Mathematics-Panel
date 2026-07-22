"""Tests for the AIManager statistical and clustering operations.

Covers linear/polynomial regression, k-means clustering, and random
point generation. Extracted from the legacy ``test_core.py`` module.
"""

import pytest


class TestAIManager:
    """Tests for the AIManager analytics facade."""

    @pytest.mark.unit
    def test_fit_linear_regression(self, ai_manager):
        points = [(1.0, 2.0), (2.0, 4.0), (3.0, 6.0)]
        result = ai_manager.fit_linear_regression(points)
        assert result["success"]
        assert result["slope"] == pytest.approx(2.0, abs=0.1)

    @pytest.mark.unit
    def test_fit_polynomial_regression(self, ai_manager):
        points = [(0.0, 0.0), (1.0, 1.0), (2.0, 4.0), (3.0, 9.0)]
        result = ai_manager.fit_polynomial_regression(points, degree=2)
        assert result["success"]

    @pytest.mark.unit
    def test_cluster_kmeans(self, ai_manager):
        points = [[1.0, 1.0], [1.5, 2.0], [5.0, 8.0], [8.0, 8.0]]
        result = ai_manager.cluster_kmeans(points, n_clusters=2)
        assert result["success"]
        assert len(result["centers"]) == 2

    @pytest.mark.unit
    def test_generate_random_points(self, ai_manager):
        result = ai_manager.generate_random_points(n=10)
        assert result["success"]
        assert len(result["points"]) == 10
