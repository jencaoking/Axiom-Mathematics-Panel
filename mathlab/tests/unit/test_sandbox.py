"""Tests for the sandbox execution environment and security guarantees.

Covers normal code execution, timeout protection, memory-limit
enforcement, sandbox isolation, and the SandboxManager factory. Merged
from the legacy ``test_core.py`` and ``test_sandbox_security.py``
modules.
"""

import pytest

from mathlab.core.sandbox import SandboxManager


class TestSandboxProcess:
    """Tests for the SandboxProcess code runner."""

    @pytest.mark.unit
    def test_run_code_success(self, sandbox):
        result = sandbox.run_code('print("test")', timeout=5)
        assert "test" in result["output"]

    @pytest.mark.unit
    def test_sandbox_timeout(self, sandbox):
        """Timeout termination mechanism works."""
        result = sandbox.run_code("while True: pass", timeout=2)
        assert result["success"] is False
        # Watchdog triggers timeout or memory limit.
        assert (
            "timed out" in result["error"].lower()
            or "Memory limit" in result["error"]
            or "execution timed out" in result["error"].lower()
        )

    @pytest.mark.unit
    def test_sandbox_memory_limit(self, sandbox):
        """Memory limit is enforced when psutil is available."""
        sandbox.max_memory_mb = 50  # Lowered threshold for fast testing.
        code = "arr = []\nwhile True:\n    arr.append('X' * 1000000)"
        result = sandbox.run_code(code, timeout=10)
        assert result["success"] is False
        # Triggers memory limit or timeout.
        assert "Memory limit" in result["error"] or "timed out" in result["error"].lower()

    @pytest.mark.unit
    def test_sandbox_normal_execution(self, sandbox):
        """Normal code with numpy executes successfully."""
        result = sandbox.run_code("print('Hello'); import numpy as np; print(np.array([1,2,3]))")
        assert result["success"] is True
        assert "Hello" in result["output"]
        assert "[1 2 3]" in result["output"]


class TestSandboxManager:
    """Tests for the SandboxManager factory."""

    @pytest.mark.unit
    def test_create_sandbox(self):
        manager = SandboxManager()
        sandbox_id = manager.create_sandbox()
        assert sandbox_id.startswith("sandbox_")


class TestNormalExecution:
    """Tests for normal sandbox code execution."""

    @pytest.mark.unit
    def test_hello_world(self, sandbox):
        result = sandbox.run_code("print('Hello World'); x = [1, 2, 3]; print(x)")
        assert result["success"] is True
        assert "Hello World" in result["output"]
        assert "[1, 2, 3]" in result["output"]

    @pytest.mark.unit
    def test_numpy_import(self, sandbox):
        result = sandbox.run_code("import numpy as np; print(np.array([1,2,3]))")
        assert result["success"] is True
        assert "[1 2 3]" in result["output"]


class TestTimeoutProtection:
    """Tests for sandbox timeout enforcement."""

    @pytest.mark.unit
    def test_infinite_loop_killed(self, sandbox):
        result = sandbox.run_code("while True: pass", timeout=2)
        assert result["success"] is False
        assert len(result["error"]) > 0


class TestMemoryProtection:
    """Tests for sandbox memory-limit enforcement."""

    @pytest.mark.unit
    @pytest.mark.slow
    def test_memory_limit(self, sandbox):
        sandbox.max_memory_mb = 50
        code = "arr = []\nwhile True:\n    arr.append('X' * 1000000)"
        result = sandbox.run_code(code, timeout=10)
        assert result["success"] is False
        assert "Memory limit" in result["error"] or "timed out" in result["error"].lower()


class TestSandboxIsolation:
    """Tests for sandbox variable isolation."""

    @pytest.mark.unit
    def test_variable_does_not_persist(self, repl):
        result1 = repl.execute("a = 42")
        assert result1["success"] is True

        result2 = repl.execute("print(a)")
        assert result2["success"] is False
        assert "name" in result2["error"].lower()
