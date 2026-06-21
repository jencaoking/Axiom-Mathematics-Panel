from .ui import MainWindow
from .core import (
    GeometryEngine, CASProvider, AlgoAnimator,
    PythonREPL, AIManager, SandboxManager
)
from .data import ProjectManager

__version__ = '2.6.0'
__author__ = 'MathLab Team'

__all__ = [
    'MainWindow',
    'GeometryEngine',
    'CASProvider',
    'AlgoAnimator',
    'PythonREPL',
    'AIManager',
    'SandboxManager',
    'ProjectManager',
]
