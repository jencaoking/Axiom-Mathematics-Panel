"""End-to-end tests for the FunctionExplorerPanel UI.

These tests drive the real ``FunctionExplorerPanel`` widget through the pytest-qt
``qtbot`` fixture to verify parameter extraction and basic UI construction.
They require a running Qt event loop (provided by pytest-qt) and are marked
``e2e`` and ``qt`` accordingly.
"""

import pytest

from mathlab.ui.function_explorer_panel import FunctionExplorerPanel


@pytest.mark.e2e
@pytest.mark.qt
def test_parameter_extraction(qtbot):
    """The panel should extract free parameters from symbolic expressions."""
    panel = FunctionExplorerPanel()
    qtbot.addWidget(panel)

    test_cases = [
        ("A*sin(omega*x + phi)", ["A", "omega", "phi"]),
        ("a*x^2 + b*x + c", ["a", "b", "c"]),
    ]

    for expr, expected in test_cases:
        params = panel._extract_parameters(expr)
        assert set(params) == set(expected), f"Expression {expr} parameter extraction failed"


@pytest.mark.e2e
@pytest.mark.qt
def test_ui_creation(qtbot):
    """The panel should construct with a valid window title and minimum width."""
    panel = FunctionExplorerPanel()
    qtbot.addWidget(panel)

    assert panel.windowTitle() is not None
    assert panel.minimumWidth() >= 0
