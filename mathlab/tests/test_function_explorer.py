"""
测试动态函数探索器功能
"""
import sys
import os
import importlib.util
import pytest

mathlab_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, mathlab_dir)

# Avoid triggering mathlab/ui/__init__.py chain
spec = importlib.util.spec_from_file_location(
    "function_explorer_panel",
    os.path.join(mathlab_dir, "ui", "function_explorer_panel.py"),
)
func_explorer_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(func_explorer_module)
FunctionExplorerPanel = func_explorer_module.FunctionExplorerPanel


def test_parameter_extraction(qtbot):
    panel = FunctionExplorerPanel()
    qtbot.addWidget(panel)

    test_cases = [
        ("A*sin(omega*x + phi)", ["A", "omega", "phi"]),
        ("a*x^2 + b*x + c", ["a", "b", "c"]),
    ]

    for expr, expected in test_cases:
        params = panel._extract_parameters(expr)
        assert set(params) == set(expected), f"Expression {expr} parameter extraction failed"


def test_ui_creation(qtbot):
    panel = FunctionExplorerPanel()
    qtbot.addWidget(panel)
    assert panel.windowTitle() is not None
    assert panel.minimumWidth() >= 0
