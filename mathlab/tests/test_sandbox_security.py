"""
沙箱安全加固核心功能测试
"""
import sys
import os
import importlib.util
import pytest

mathlab_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, mathlab_dir)

spec = importlib.util.spec_from_file_location(
    "sandbox", os.path.join(mathlab_dir, "core", "sandbox.py")
)
sandbox_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sandbox_module)
SandboxProcess = sandbox_module.SandboxProcess


@pytest.fixture
def sandbox():
    s = SandboxProcess()
    yield s
    try:
        s.terminate()
    except Exception:
        pass


class TestNormalExecution:
    def test_hello_world(self, sandbox):
        result = sandbox.run_code("print('Hello World'); x = [1, 2, 3]; print(x)")
        assert result["success"] is True
        assert "Hello World" in result["output"]
        assert "[1, 2, 3]" in result["output"]

    def test_numpy_import(self, sandbox):
        result = sandbox.run_code("import numpy as np; print(np.array([1,2,3]))")
        assert result["success"] is True
        assert "[1 2 3]" in result["output"]


class TestTimeoutProtection:
    def test_infinite_loop_killed(self, sandbox):
        result = sandbox.run_code("while True: pass", timeout=2)
        assert result["success"] is False
        assert len(result["error"]) > 0


class TestMemoryProtection:
    @pytest.mark.slow
    def test_memory_limit(self):
        sandbox = SandboxProcess()
        sandbox.max_memory_mb = 50
        code = "arr = []\nwhile True:\n    arr.append('X' * 1000000)"
        result = sandbox.run_code(code, timeout=10)
        assert result["success"] is False
        assert "Memory limit" in result["error"] or "timed out" in result["error"].lower()


class TestSandboxIsolation:
    def test_variable_does_not_persist(self):
        from mathlab.core.python_repl import PythonREPL
        repl = PythonREPL(session_mode=False)

        result1 = repl.execute("a = 42")
        assert result1["success"] is True

        result2 = repl.execute("print(a)")
        assert result2["success"] is False
        assert "name" in result2["error"].lower()
