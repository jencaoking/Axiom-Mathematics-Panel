"""mathlab.core — lazy import facade.

Uses __getattr__ to defer Qt-dependent module imports until first access.
This allows tests and scripts to import individual core submodules
(e.g. ``from mathlab.core.geometry_engine import GeometryEngine``)
without triggering the full PySide6 import chain.
"""

__all__ = [
    "GeometryEngine",
    "GeometricObject",
    "Point",
    "Segment",
    "Circle",
    "CASProvider",
    "AlgoAnimator",
    "PythonREPL",
    "AIManager",
    "SandboxProcess",
    "SandboxManager",
    "GeometrySignals",
    "ConsoleSignals",
    "AlgorithmSignals",
    "AISignals",
    "MathLabAPI",
    "MathLabPlugin",
    "PluginManager",
    "AgentUIBridge",
]


def __getattr__(name):
    _mapping = {
        "GeometryEngine": ".geometry_engine",
        "GeometricObject": ".geometry_engine",
        "Point": ".geometry_engine",
        "Segment": ".geometry_engine",
        "Circle": ".geometry_engine",
        "CASProvider": ".cas_provider",
        "AlgoAnimator": ".algo_animator",
        "PythonREPL": ".python_repl",
        "AIManager": ".ai_manager",
        "SandboxProcess": ".sandbox",
        "SandboxManager": ".sandbox",
        "GeometrySignals": ".signals",
        "ConsoleSignals": ".signals",
        "AlgorithmSignals": ".signals",
        "AISignals": ".signals",
        "MathLabAPI": ".extension_api",
        "MathLabPlugin": ".plugin_base",
        "PluginManager": ".plugin_manager",
        "AgentUIBridge": ".agent_bridge",
    }
    if name in _mapping:
        import importlib

        mod = importlib.import_module(_mapping[name], __package__)
        return getattr(mod, name)
    raise AttributeError(f"module 'mathlab.core' has no attribute {name!r}")
