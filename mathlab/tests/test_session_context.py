"""
会话上下文传递功能测试
验证 REPL 在会话模式/隔离模式下的变量持久化行为
"""
import sys
import os
import importlib.util
import pytest

mathlab_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, mathlab_dir)

core_path = os.path.join(mathlab_dir, "core")

sandbox_spec = importlib.util.spec_from_file_location("sandbox", os.path.join(core_path, "sandbox.py"))
sandbox_module = importlib.util.module_from_spec(sandbox_spec)
sys.modules["sandbox"] = sandbox_module
sandbox_spec.loader.exec_module(sandbox_module)

repl_spec = importlib.util.spec_from_file_location("python_repl", os.path.join(core_path, "python_repl.py"))
python_repl_module = importlib.util.module_from_spec(repl_spec)
repl_spec.loader.exec_module(python_repl_module)
PythonREPL = python_repl_module.PythonREPL


@pytest.fixture
def session_repl():
    return PythonREPL(session_mode=True)


@pytest.fixture
def isolated_repl():
    return PythonREPL(session_mode=False)


class TestSessionModePersistence:
    def test_variable_persists(self, session_repl):
        result1 = session_repl.execute("x = 42")
        assert result1["success"]

        result2 = session_repl.execute("print(x * 2)")
        assert result2["success"]
        assert "84" in result2["output"]

    def test_function_persists(self, session_repl):
        session_repl.execute("def double(n): return n * 2")
        result = session_repl.execute("print(double(21))")
        assert result["success"]
        assert "42" in result["output"]

    def test_complex_math(self, session_repl):
        session_repl.execute("numbers = [1, 2, 3, 4, 5]")
        session_repl.execute("total = sum(numbers)")
        session_repl.execute("average = total / len(numbers)")
        result = session_repl.execute('print(f"Sum: {total}, Average: {average}")')
        assert result["success"]
        assert "Sum: 15" in result["output"]
        assert "Average: 3.0" in result["output"]


class TestIsolationMode:
    def test_variable_does_not_persist(self, isolated_repl):
        isolated_repl.execute("y = 100")
        result = isolated_repl.execute("print(y)")
        assert not result["success"]
        assert "name" in result["error"].lower()


class TestModeSwitching:
    def test_switch_to_isolation_clears_context(self, session_repl):
        session_repl.execute("z = 999")
        result1 = session_repl.execute("print(z)")
        assert result1["success"] and "999" in result1["output"]

        session_repl.set_session_mode(False)
        result2 = session_repl.execute("print(z)")
        assert not result2["success"]


class TestClearSession:
    def test_clear_removes_all_variables(self, session_repl):
        session_repl.execute("a = 1; b = 2; c = 3")
        result = session_repl.execute("print(a + b + c)")
        assert "6" in result["output"]

        session_repl.clear_session()
        assert session_repl.get_session_context_length() == 0

        result2 = session_repl.execute("print(a)")
        assert not result2["success"]
