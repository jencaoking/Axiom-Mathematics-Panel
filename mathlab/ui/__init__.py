"""mathlab.ui — lazy import facade.

Uses __getattr__ to defer widget imports until first access.
This allows tests to import individual UI modules
(e.g. ``from mathlab.ui.function_explorer_panel import FunctionExplorerPanel``)
without triggering the full PySide6 widget import chain.
"""

__all__ = [
    "MainWindow",
    "GeometryCanvas",
    "AlgebraPanel",
    "PythonConsole",
    "PropertiesPanel",
    "CommandBar",
    "AlgoVisPanel",
    "AIToolsPanel",
    "AutocompleteTextEdit",
]


def __getattr__(name):
    _mapping = {
        "MainWindow": ".main_window",
        "GeometryCanvas": ".canvas",
        "AlgebraPanel": ".algebra_panel",
        "PythonConsole": ".console",
        "PropertiesPanel": ".properties_panel",
        "CommandBar": ".command_bar",
        "AlgoVisPanel": ".algo_vis_panel",
        "AIToolsPanel": ".ai_tools_panel",
        "AutocompleteTextEdit": ".code_editor",
    }
    if name in _mapping:
        import importlib

        mod = importlib.import_module(_mapping[name], __package__)
        return getattr(mod, name)
    raise AttributeError(f"module 'mathlab.ui' has no attribute {name!r}")
