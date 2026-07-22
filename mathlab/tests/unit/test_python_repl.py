"""Tests for the PythonREPL execution context.

Covers basic execution, output capture, history tracking, and the
sandbox/session-mode isolation semantics. Merged from the legacy
``test_core.py`` and ``test_session_context.py`` modules.
"""

import pytest


class TestPythonREPL:
    """Tests for PythonREPL in isolated (non-session) mode."""

    @pytest.mark.unit
    def test_execute_simple(self, repl):
        """Isolated mode executes simple code."""
        result = repl.execute("x = 5")
        assert result["success"]
        # Isolated mode does not persist variables, so the namespace
        # cannot be inspected across executions.

    @pytest.mark.unit
    def test_execute_with_output(self, repl):
        """Output capture works."""
        result = repl.execute('print("hello")')
        assert "hello" in result["output"]

    @pytest.mark.unit
    def test_history(self, repl):
        """History is recorded across executions."""
        repl.execute("x = 1")
        repl.execute("y = 2")
        history = repl.get_history()
        assert len(history) == 2

    @pytest.mark.unit
    def test_sandbox_isolation(self, repl):
        """Each execution runs in an independent environment."""
        result1 = repl.execute("a = 10")
        assert result1["success"]

        # On the second execution, ``a`` is no longer defined.
        result2 = repl.execute("print(a)")
        assert not result2["success"]
        assert "name" in result2["error"].lower()


class TestSessionModePersistence:
    """Tests for variable/function persistence in session mode."""

    @pytest.mark.unit
    def test_variable_persists(self, session_repl):
        result1 = session_repl.execute("x = 42")
        assert result1["success"]

        result2 = session_repl.execute("print(x * 2)")
        assert result2["success"]
        assert "84" in result2["output"]

    @pytest.mark.unit
    def test_function_persists(self, session_repl):
        session_repl.execute("def double(n): return n * 2")
        result = session_repl.execute("print(double(21))")
        assert result["success"]
        assert "42" in result["output"]

    @pytest.mark.unit
    def test_complex_math(self, session_repl):
        session_repl.execute("numbers = [1, 2, 3, 4, 5]")
        session_repl.execute("total = sum(numbers)")
        session_repl.execute("average = total / len(numbers)")
        result = session_repl.execute('print(f"Sum: {total}, Average: {average}")')
        assert result["success"]
        assert "Sum: 15" in result["output"]
        assert "Average: 3.0" in result["output"]


class TestIsolationMode:
    """Tests for isolation-mode non-persistence."""

    @pytest.mark.unit
    def test_variable_does_not_persist(self, repl):
        repl.execute("y = 100")
        result = repl.execute("print(y)")
        assert not result["success"]
        assert "name" in result["error"].lower()


class TestModeSwitching:
    """Tests for switching between session and isolation modes."""

    @pytest.mark.unit
    def test_switch_to_isolation_clears_context(self, session_repl):
        session_repl.execute("z = 999")
        result1 = session_repl.execute("print(z)")
        assert result1["success"] and "999" in result1["output"]

        session_repl.set_session_mode(False)
        result2 = session_repl.execute("print(z)")
        assert not result2["success"]


class TestClearSession:
    """Tests for clearing the session context."""

    @pytest.mark.unit
    def test_clear_removes_all_variables(self, session_repl):
        session_repl.execute("a = 1; b = 2; c = 3")
        result = session_repl.execute("print(a + b + c)")
        assert "6" in result["output"]

        session_repl.clear_session()
        assert session_repl.get_session_context_length() == 0

        result2 = session_repl.execute("print(a)")
        assert not result2["success"]
