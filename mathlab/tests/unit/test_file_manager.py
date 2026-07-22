"""Tests for the FileManager project persistence and search layer.

Covers project creation/opening, recent-project retrieval, and the
SearchFilter matching logic. Extracted from the legacy ``test_core.py``
module.
"""

import os

import pytest

from mathlab.data.file_manager import FileCategory, SearchFilter


class TestFileManager:
    """Tests for the FileManager project CRUD operations."""

    @pytest.mark.unit
    def test_create_project(self, file_manager):
        result = file_manager.create_project("Test Project", FileCategory.GEOMETRY)
        assert result["success"]
        assert os.path.exists(result["file_path"])

    @pytest.mark.unit
    def test_open_project(self, file_manager):
        create_result = file_manager.create_project("Test Project")
        result = file_manager.open_project(create_result["file_path"])
        assert result["success"]

    @pytest.mark.unit
    def test_search_projects(self, file_manager):
        file_manager.create_project("Geometry Project", FileCategory.GEOMETRY)
        file_manager.create_project("Algebra Project", FileCategory.ALGEBRA)

        search_filter = SearchFilter()
        search_filter.category = FileCategory.GEOMETRY.value
        results = file_manager.search_projects(search_filter)
        assert len(results) >= 1

    @pytest.mark.unit
    def test_get_recent_projects(self, file_manager):
        file_manager.create_project("Recent 1")
        file_manager.create_project("Recent 2")
        recent = file_manager.get_recent_projects(limit=5)
        assert len(recent) >= 2


class TestSearchFilter:
    """Tests for the SearchFilter matching predicates."""

    @pytest.mark.unit
    def test_matches_query(self):
        filter = SearchFilter()
        filter.query = "test"
        entry = {"name": "test_project", "category": "geometry"}
        assert filter.matches(entry)

    @pytest.mark.unit
    def test_matches_category(self):
        filter = SearchFilter()
        filter.category = "geometry"
        entry = {"name": "test", "category": "geometry"}
        assert filter.matches(entry)

    @pytest.mark.unit
    def test_matches_object_types(self):
        filter = SearchFilter()
        filter.object_types = ["Point", "Circle"]
        entry = {"name": "test", "object_types": ["Point", "Segment"]}
        assert filter.matches(entry)
