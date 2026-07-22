"""Tests for the AlgoAnimator step-through animation engine.

Covers algorithm loading, single-step advancement, and reset behavior
for all 8 visualization algorithms, plus description i18n verification.
Extracted from the legacy ``test_core.py`` module.
"""

import pytest

from mathlab.core.algo_animator import NX_AVAILABLE

# Skip marker for graph algorithms that require networkx
requires_networkx = pytest.mark.skipif(not NX_AVAILABLE, reason="networkx not installed")


class TestAlgoAnimator:
    """Tests for the AlgoAnimator visualization engine."""

    @pytest.mark.unit
    def test_load_algorithm(self, animator):
        result = animator.load_algorithm("bubble_sort", arr=[5, 3, 8, 1])
        assert result
        assert animator.current_algorithm == "bubble_sort"

    @pytest.mark.unit
    def test_step(self, animator):
        animator.load_algorithm("bubble_sort", arr=[5, 3, 8, 1])
        state = animator.step()
        assert state is not None
        assert state["type"] == "sorting"

    @pytest.mark.unit
    def test_reset(self, animator):
        animator.load_algorithm("bubble_sort", arr=[5, 3, 8, 1])
        animator.step()
        animator.reset()
        assert animator.current_state is None

    # ------------------------------------------------------------------
    # Quick Sort
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_quick_sort_load_and_step(self, animator):
        assert animator.load_algorithm("quick_sort", arr=[5, 3, 8, 1])
        state = animator.step()
        assert state is not None
        assert state["type"] == "sorting"

    @pytest.mark.unit
    def test_quick_sort_completes(self, animator):
        animator.load_algorithm("quick_sort", arr=[5, 3, 8, 1])
        states = []
        while True:
            state = animator.step()
            if state is None:
                break
            states.append(state)
        assert states[-1]["sorted"] == list(range(4))

    # ------------------------------------------------------------------
    # Binary Search
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_binary_search_load_and_step(self, animator):
        arr = [1, 3, 5, 7, 9, 11]
        assert animator.load_algorithm("binary_search", arr=arr, target=7)
        state = animator.step()
        assert state is not None
        assert state["type"] == "search"

    @pytest.mark.unit
    def test_binary_search_finds_target(self, animator):
        arr = [1, 3, 5, 7, 9, 11]
        animator.load_algorithm("binary_search", arr=arr, target=7)
        found_state = None
        while True:
            state = animator.step()
            if state is None:
                break
            if state.get("found"):
                found_state = state
        assert found_state is not None
        assert found_state["found"] is True

    # ------------------------------------------------------------------
    # BFS
    # ------------------------------------------------------------------

    @pytest.mark.unit
    @requires_networkx
    def test_bfs_load_and_step(self, animator):
        import networkx as nx

        graph = nx.path_graph(4)
        assert animator.load_algorithm("bfs", graph=graph, start=0)
        state = animator.step()
        assert state is not None
        assert state["type"] == "graph"

    @pytest.mark.unit
    @requires_networkx
    def test_bfs_visits_all_nodes(self, animator):
        import networkx as nx

        graph = nx.path_graph(4)
        animator.load_algorithm("bfs", graph=graph, start=0)
        last_state = None
        while True:
            state = animator.step()
            if state is None:
                break
            last_state = state
        assert last_state is not None
        assert len(last_state["order"]) == 4

    # ------------------------------------------------------------------
    # DFS
    # ------------------------------------------------------------------

    @pytest.mark.unit
    @requires_networkx
    def test_dfs_load_and_step(self, animator):
        import networkx as nx

        graph = nx.path_graph(4)
        assert animator.load_algorithm("dfs", graph=graph, start=0)
        state = animator.step()
        assert state is not None
        assert state["type"] == "graph"

    @pytest.mark.unit
    @requires_networkx
    def test_dfs_visits_all_nodes(self, animator):
        import networkx as nx

        graph = nx.path_graph(4)
        animator.load_algorithm("dfs", graph=graph, start=0)
        last_state = None
        while True:
            state = animator.step()
            if state is None:
                break
            last_state = state
        assert last_state is not None
        assert len(last_state["order"]) == 4

    # ------------------------------------------------------------------
    # Dijkstra
    # ------------------------------------------------------------------

    @pytest.mark.unit
    @requires_networkx
    def test_dijkstra_load_and_step(self, animator):
        import networkx as nx

        graph = nx.path_graph(4)
        for u, v in graph.edges():
            graph[u][v]["weight"] = 1
        assert animator.load_algorithm("dijkstra", graph=graph, start=0)
        state = animator.step()
        assert state is not None
        assert state["type"] == "shortest_path"

    @pytest.mark.unit
    @requires_networkx
    def test_dijkstra_distances(self, animator):
        import networkx as nx

        graph = nx.path_graph(4)
        for u, v in graph.edges():
            graph[u][v]["weight"] = 1
        animator.load_algorithm("dijkstra", graph=graph, start=0)
        last_state = None
        while True:
            state = animator.step()
            if state is None:
                break
            last_state = state
        assert last_state is not None
        assert last_state["distances"][0] == 0
        assert last_state["distances"][3] == 3

    # ------------------------------------------------------------------
    # Convex Hull
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_convex_hull_load_and_step(self, animator):
        points = [(0, 0), (1, 0), (0, 1), (1, 1)]
        assert animator.load_algorithm("convex_hull", points=points)
        state = animator.step()
        assert state is not None
        assert state["type"] == "convex_hull"

    @pytest.mark.unit
    def test_convex_hull_completes(self, animator):
        points = [(0, 0), (4, 0), (0, 4), (4, 4), (2, 2)]
        animator.load_algorithm("convex_hull", points=points)
        last_state = None
        while True:
            state = animator.step()
            if state is None:
                break
            last_state = state
        assert last_state is not None
        assert len(last_state["hull"]) >= 3

    # ------------------------------------------------------------------
    # K-means
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_kmeans_load_and_step(self, animator):
        points = [(0, 0), (1, 0), (0, 1), (10, 10), (11, 10), (10, 11)]
        assert animator.load_algorithm("kmeans", points=points, k=2)
        state = animator.step()
        assert state is not None
        assert state["type"] == "clustering"

    @pytest.mark.unit
    def test_kmeans_completes(self, animator):
        points = [(0, 0), (1, 0), (0, 1), (10, 10), (11, 10), (10, 11)]
        animator.load_algorithm("kmeans", points=points, k=2)
        last_state = None
        while True:
            state = animator.step()
            if state is None:
                break
            last_state = state
        assert last_state is not None
        assert len(last_state["centers"]) == 2

    @pytest.mark.unit
    def test_kmeans_too_few_points(self, animator):
        points = [(0, 0), (1, 1)]
        assert animator.load_algorithm("kmeans", points=points, k=5)
        state = animator.step()
        assert state is not None
        assert state["type"] == "error"

    # ------------------------------------------------------------------
    # Description i18n
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_description_is_translated_string(self, animator):
        """Description should be a non-empty translated string, not a raw key."""
        animator.load_algorithm("bubble_sort", arr=[5, 3, 8, 1])
        state = animator.step()
        assert state["description"]
        assert isinstance(state["description"], str)

    @pytest.mark.unit
    def test_descriptions_switch_with_language(self, animator):
        """Verify description text changes when UI language changes (i18n)."""
        from mathlab.utils.i18n_manager import get_i18n

        i18n = get_i18n()
        original_lang = i18n.get_language()

        try:
            i18n.set_language("en")
            animator.load_algorithm("bubble_sort", arr=[5, 3, 8, 1])
            desc_en = animator.step()["description"]

            i18n.set_language("zh")
            animator.reset()
            desc_zh = animator.step()["description"]

            # Descriptions should differ between languages
            assert desc_en != desc_zh
        finally:
            i18n.set_language(original_lang)
