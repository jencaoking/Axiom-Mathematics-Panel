"""Integration test configuration.

These tests verify multi-component interactions — e.g. OctaveBridge → NumEngine
routing, or GeometryEngine + DAG cascading operations — that span more than one
collaborating module. They rely on the shared fixtures provided by the root
``mathlab/tests/conftest.py`` and do not define additional fixtures themselves.
"""
