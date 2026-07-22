"""Integration tests for GeometryEngine + DAG cascading operations.

These tests exercise the interaction between ``GeometryEngine`` (which owns the
object store) and the ``DAG`` (which tracks parent → child dependencies) to
verify cascading deletes, dependency traversal, serialization round-trips and
mixed-type queries behave correctly end-to-end.

The ``engine`` fixture is provided by the root conftest.
"""

import pytest

from mathlab.core.geometry_engine import GeometryEngine


@pytest.mark.integration
def test_cascading_delete_segment(engine):
    """Deleting a point should cascade-remove the segment that depends on it."""
    p1_id = engine.add_point(0.0, 0.0, name="A")
    p2_id = engine.add_point(1.0, 1.0, name="B")
    seg_id = engine.add_segment(p1_id, p2_id, name="AB")

    assert seg_id in engine.objects
    engine.remove_object(p1_id)

    # Segment depended on the deleted point and must be cascade-removed.
    assert seg_id not in engine.objects
    # The other point survives — only direct dependents are cascaded.
    assert p2_id in engine.objects


@pytest.mark.integration
def test_cascading_delete_circle(engine):
    """Deleting the center point should cascade-remove the circle."""
    center_id = engine.add_point(2.0, 3.0, name="O")
    circle_id = engine.add_circle(center_id, radius=1.5, name="C1")

    assert circle_id in engine.objects
    engine.remove_object(center_id)

    assert circle_id not in engine.objects


@pytest.mark.integration
def test_cascading_delete_polygon(engine):
    """Deleting any vertex should cascade-remove the polygon."""
    p1_id = engine.add_point(0.0, 0.0, name="P1")
    p2_id = engine.add_point(1.0, 0.0, name="P2")
    p3_id = engine.add_point(0.5, 1.0, name="P3")
    poly_id = engine.add_polygon([p1_id, p2_id, p3_id], name="Tri")

    assert poly_id in engine.objects
    engine.remove_object(p2_id)

    assert poly_id not in engine.objects
    # The two non-deleted vertices remain.
    assert p1_id in engine.objects
    assert p3_id in engine.objects


@pytest.mark.integration
def test_dependency_chain(engine):
    """get_dependencies must return parents in topological order before the node.

    We build the chain: point A, point B, segment AB (depends on both A and B).
    The dependency walk for the segment must list both points before the
    segment itself.
    """
    a_id = engine.add_point(0.0, 0.0, name="A")
    b_id = engine.add_point(1.0, 0.0, name="B")
    seg_id = engine.add_segment(a_id, b_id, name="AB")

    deps = engine.dependencies.get_dependencies(seg_id)

    # Both parent points are part of the dependency closure.
    assert a_id in deps
    assert b_id in deps
    # Topological invariant: parents appear before the segment.
    assert deps.index(a_id) < deps.index(seg_id)
    assert deps.index(b_id) < deps.index(seg_id)
    # The queried node is the last element (leaf of the dependency walk).
    assert deps[-1] == seg_id


@pytest.mark.integration
def test_bulk_operations(engine):
    """Serialize a populated engine and deserialize into a fresh one.

    All objects (points, segments, circles, polygons) must survive the
    round-trip with their IDs and types intact.
    """
    p1 = engine.add_point(0.0, 0.0, name="A")
    p2 = engine.add_point(1.0, 0.0, name="B")
    p3 = engine.add_point(0.5, 1.0, name="C")
    seg = engine.add_segment(p1, p2, name="AB")
    circ = engine.add_circle(p3, radius=2.0, name="Circ")
    poly = engine.add_polygon([p1, p2, p3], name="Tri")

    serialized = engine.serialize_all()
    assert serialized["objects"]  # sanity: not empty

    new_engine = GeometryEngine()
    new_engine.deserialize_all(serialized)

    # Every original object ID is present in the reconstructed engine.
    for obj_id in (p1, p2, p3, seg, circ, poly):
        assert obj_id in new_engine.objects

    # Types are preserved across the round-trip.
    assert new_engine.get_object(p1).type == "Point"
    assert new_engine.get_object(seg).type == "Segment"
    assert new_engine.get_object(circ).type == "Circle"
    assert new_engine.get_object(poly).type == "Polygon"

    # Total object count matches.
    assert len(new_engine.objects) == len(engine.objects)


@pytest.mark.integration
def test_mixed_object_types(engine):
    """get_objects_by_type must filter correctly across a mixed scene."""
    p1 = engine.add_point(0.0, 0.0, name="A")
    p2 = engine.add_point(1.0, 0.0, name="B")
    p3 = engine.add_point(0.0, 1.0, name="C")
    p4 = engine.add_point(1.0, 1.0, name="D")

    engine.add_segment(p1, p2, name="AB")
    engine.add_segment(p3, p4, name="CD")
    engine.add_circle(p1, radius=1.0, name="C1")
    engine.add_circle(p2, radius=2.0, name="C2")
    engine.add_polygon([p1, p2, p3], name="Tri1")
    engine.add_polygon([p2, p3, p4], name="Tri2")

    points = engine.get_objects_by_type("Point")
    segments = engine.get_objects_by_type("Segment")
    circles = engine.get_objects_by_type("Circle")
    polygons = engine.get_objects_by_type("Polygon")

    assert len(points) == 4
    assert len(segments) == 2
    assert len(circles) == 2
    assert len(polygons) == 2

    # Names round-trip correctly per type.
    assert {obj.name for obj in points} == {"A", "B", "C", "D"}
    assert {obj.name for obj in segments} == {"AB", "CD"}
    assert {obj.name for obj in circles} == {"C1", "C2"}
    assert {obj.name for obj in polygons} == {"Tri1", "Tri2"}
