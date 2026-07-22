"""Tests for the dependency DAG used by the geometry engine.

Verifies edge insertion, node removal, and dependency/dependent lookups.
Extracted from the legacy ``test_core.py`` module.
"""

import pytest


class TestDAG:
    """Tests for the DAG dependency-tracking structure."""

    @pytest.mark.unit
    def test_add_edge(self, dag):
        dag.add_edge("A", "B")
        assert "B" in dag.graph["A"]
        assert "A" in dag.reverse_graph["B"]

    @pytest.mark.unit
    def test_remove_node(self, dag):
        dag.add_edge("A", "B")
        dag.add_edge("B", "C")
        dag.remove_node("B")

        assert "B" not in dag.graph
        assert "B" not in dag.reverse_graph

    @pytest.mark.unit
    def test_get_dependencies(self, dag):
        dag.add_edge("A", "C")
        dag.add_edge("B", "C")
        deps = dag.get_dependencies("C")
        assert "A" in deps
        assert "B" in deps

    @pytest.mark.unit
    def test_get_dependents(self, dag):
        dag.add_edge("A", "B")
        dag.add_edge("A", "C")
        deps = dag.get_dependents("A")
        assert "B" in deps
        assert "C" in deps
