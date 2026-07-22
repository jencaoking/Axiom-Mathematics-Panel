"""Root conftest — shared fixtures, markers, and environment setup.

This is the single entry point for the unified testing system.
All test tiers (unit, integration, e2e) inherit fixtures defined here.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest

# ─── Environment ────────────────────────────────────────────────────────
# Headless Qt: no X11/OpenGL/Wayland display needed.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Ensure project root is on sys.path so ``import mathlab`` works.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ─── Markers ────────────────────────────────────────────────────────────
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: fast isolated unit tests")
    config.addinivalue_line("markers", "integration: multi-component integration tests")
    config.addinivalue_line("markers", "e2e: end-to-end UI tests requiring Qt event loop")
    config.addinivalue_line("markers", "slow: tests that take >2s (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "qt: tests that require a Qt event loop")


# ─── Shared Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def engine():
    """Fresh GeometryEngine instance for each test."""
    from mathlab.core.geometry_engine import GeometryEngine

    return GeometryEngine()


@pytest.fixture
def dag():
    """Fresh DAG instance."""
    from mathlab.core.geometry_engine import DAG

    return DAG()


@pytest.fixture
def cas():
    """Fresh CASProvider instance."""
    from mathlab.core.cas_provider import CASProvider

    return CASProvider()


@pytest.fixture
def repl():
    """Fresh PythonREPL in isolated (non-session) mode."""
    from mathlab.core.python_repl import PythonREPL

    return PythonREPL(session_mode=False)


@pytest.fixture
def session_repl():
    """Fresh PythonREPL in session (persistent) mode."""
    from mathlab.core.python_repl import PythonREPL

    return PythonREPL(session_mode=True)


@pytest.fixture
def sandbox():
    """Fresh SandboxProcess; auto-terminated after test."""
    from mathlab.core.sandbox import SandboxProcess

    s = SandboxProcess()
    yield s
    try:
        s.terminate()
    except Exception:
        pass


@pytest.fixture
def ai_manager():
    """Fresh AIManager instance."""
    from mathlab.core.ai_manager import AIManager

    return AIManager()


@pytest.fixture
def animator():
    """Fresh AlgoAnimator instance."""
    from mathlab.core.algo_animator import AlgoAnimator

    return AlgoAnimator()


@pytest.fixture
def num_engine():
    """Fresh NumEngine instance."""
    from mathlab.core.num_engine import NumEngine

    return NumEngine()


@pytest.fixture
def bridge():
    """Fresh OctaveBridge instance."""
    from mathlab.core.octave_bridge import OctaveBridge

    return OctaveBridge()


@pytest.fixture
def temp_dir():
    """Temporary directory; auto-cleaned after test."""
    path = tempfile.mkdtemp(prefix="mathlab_test_")
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def file_manager(temp_dir):
    """Fresh FileManager rooted in a temp directory."""
    from mathlab.data.file_manager import FileManager

    return FileManager(base_directory=temp_dir)
