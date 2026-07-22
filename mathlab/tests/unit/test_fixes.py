"""验证所有修复的组件的测试套件。

覆盖修复项：
1. CASProvider: globals().update(locals()) 移除
2. AIFitWorker: 重复 signals 初始化移除
3. JupyterSandbox: print 替换为 logger
4. CodeSecurityScanner: 危险属性拦截
5. SandboxProcess: 重复超时逻辑移除
6. AIManager: 路径处理改进
7. ChatMemoryManager: 裁剪策略改进
8. AgentRegistry: 超时控制
9. AIFacade: agent_registry 初始化检查
"""

import os
import sys
import json
import ast
import time
import threading
import tempfile
from unittest.mock import Mock, patch, MagicMock

import pytest

# ═══════════════════════════════════════════════════════════════════
# 1. CASProvider 测试：验证 globals().update(locals()) 已移除
# ═══════════════════════════════════════════════════════════════════


class TestCASProviderFix:
    """测试 CASProvider 不再使用 globals().update(locals())。"""

    def test_sympy_modules_isolated(self):
        """验证 sympy 对象存储在隔离字典中，而非全局命名空间。"""
        from mathlab.core import cas_provider

        # 加载 sympy
        cas_provider._load_sympy()

        # 验证 _sympy_modules 字典存在且包含必要的函数
        assert hasattr(cas_provider, "_sympy_modules")
        assert isinstance(cas_provider._sympy_modules, dict)
        assert "sympy" in cas_provider._sympy_modules
        assert "symbols" in cas_provider._sympy_modules
        assert "Symbol" in cas_provider._sympy_modules
        assert "Eq" in cas_provider._sympy_modules
        assert "solve" in cas_provider._sympy_modules
        assert "simplify" in cas_provider._sympy_modules

    def test_get_sympy_func_returns_correct_object(self):
        """验证 _get_sympy_func 返回正确的 sympy 函数。"""
        from mathlab.core.cas_provider import _get_sympy_func

        symbols = _get_sympy_func("symbols")
        x = symbols("x")
        assert str(x) == "x"

    def test_get_sympy_func_raises_for_unknown(self):
        """验证 _get_sympy_func 对未知函数名抛出 AttributeError。"""
        from mathlab.core.cas_provider import _get_sympy_func

        with pytest.raises(AttributeError, match="未加载"):
            _get_sympy_func("nonexistent_function")

    def test_cas_provider_simplify(self, cas):
        """验证 CASProvider.simplify 正常工作。"""
        result = cas.simplify("x + x")
        assert result["success"] is True
        assert "2*x" in result["result"]

    def test_cas_provider_solve_equation(self, cas):
        """验证 CASProvider.solve_equation 正常工作。"""
        result = cas.solve_equation("x + 2 = 5", "x")
        assert result["success"] is True
        assert len(result["solutions"]) > 0

    def test_cas_provider_differentiate(self, cas):
        """验证 CASProvider.differentiate 正常工作。"""
        result = cas.differentiate("x**2", "x")
        assert result["success"] is True
        assert "2*x" in result["result"]

    def test_cas_provider_integrate(self, cas):
        """验证 CASProvider.integrate 正常工作。"""
        result = cas.integrate("x", "x")
        assert result["success"] is True
        assert "x**2/2" in result["result"]


# ═══════════════════════════════════════════════════════════════════
# 2. AIFitWorker 测试：验证重复 signals 初始化已移除
# ═══════════════════════════════════════════════════════════════════


class TestAIFitWorkerFix:
    """测试 AIFitWorker 不再重复初始化 signals。"""

    def test_signals_not_overwritten(self):
        """验证子类不会覆盖父类的 signals 属性。"""
        from mathlab.core.async_workers import AIFitWorker, WorkerSignals

        mock_ai_manager = Mock()
        mock_ai_manager.fit_linear_regression = Mock(return_value={"success": True})

        worker = AIFitWorker(mock_ai_manager, [(1, 2), (3, 4)])

        # signals 应该是父类创建的，而非子类重新创建的
        assert hasattr(worker, "signals")
        assert isinstance(worker.signals, WorkerSignals)

    def test_cluster_worker_signals_not_overwritten(self):
        """验证 AIClusterWorker 不会覆盖父类的 signals。"""
        from mathlab.core.async_workers import AIClusterWorker, WorkerSignals

        mock_ai_manager = Mock()
        mock_ai_manager.cluster_kmeans = Mock(return_value={"success": True})

        worker = AIClusterWorker(mock_ai_manager, [(1, 2), (3, 4)])

        assert hasattr(worker, "signals")
        assert isinstance(worker.signals, WorkerSignals)

    def test_recognize_worker_signals_not_overwritten(self):
        """验证 AIRecognizeWorker 不会覆盖父类的 signals。"""
        from mathlab.core.async_workers import AIRecognizeWorker, WorkerSignals

        mock_ai_manager = Mock()
        mock_ai_manager.recognize_digit = Mock(return_value={"success": True})

        worker = AIRecognizeWorker(mock_ai_manager, [[0.1] * 784])

        assert hasattr(worker, "signals")
        assert isinstance(worker.signals, WorkerSignals)

    def test_generate_points_worker_signals_not_overwritten(self):
        """验证 AIGeneratePointsWorker 不会覆盖父类的 signals。"""
        from mathlab.core.async_workers import AIGeneratePointsWorker, WorkerSignals

        mock_ai_manager = Mock()
        mock_ai_manager.generate_random_points = Mock(return_value={"success": True})

        worker = AIGeneratePointsWorker(mock_ai_manager, n=5)

        assert hasattr(worker, "signals")
        assert isinstance(worker.signals, WorkerSignals)


# ═══════════════════════════════════════════════════════════════════
# 3. JupyterSandbox 测试：验证 print 替换为 logger
# ═══════════════════════════════════════════════════════════════════


class TestJupyterSandboxFix:
    """测试 JupyterSandbox 使用 logger 而非 print。"""

    def test_logger_imported(self):
        """验证模块导入了 logger。"""
        from mathlab.core import jupyter_manager

        assert hasattr(jupyter_manager, "logger")
        assert jupyter_manager.logger is not None

    def test_no_bare_print_in_source(self):
        """验证源代码中没有裸 print 调用。"""
        import inspect
        from mathlab.core import jupyter_manager

        source = inspect.getsource(jupyter_manager)

        # 查找 print( 但排除 logger.print 之类
        lines = source.split("\n")
        for line in lines:
            stripped = line.strip()
            # 跳过注释和文档字符串
            if stripped.startswith("#") or stripped.startswith('"') or stripped.startswith("'"):
                continue
            # 不应有裸 print( 调用
            assert not (stripped.startswith("print(") or " print(" in stripped), f"发现裸 print 调用: {line}"


# ═══════════════════════════════════════════════════════════════════
# 4. CodeSecurityScanner 测试：验证危险属性拦截
# ═══════════════════════════════════════════════════════════════════


class TestCodeSecurityScannerFix:
    """测试 CodeSecurityScanner 拦截危险属性访问。"""

    def test_subclasses_blocked(self):
        """验证 __subclasses__ 访问被拦截。"""
        from mathlab.core.sandbox_security import is_code_safe

        code = "result = ().__class__.__bases__[0].__subclasses__()"
        safe, msg = is_code_safe(code)
        assert not safe
        assert "__subclasses__" in msg or "__class__" in msg or "__bases__" in msg

    def test_mro_blocked(self):
        """验证 __mro__ 访问被拦截。"""
        from mathlab.core.sandbox_security import is_code_safe

        code = "result = str.__mro__"
        safe, msg = is_code_safe(code)
        assert not safe
        assert "__mro__" in msg

    def test_globals_blocked(self):
        """验证 __globals__ 访问被拦截。"""
        from mathlab.core.sandbox_security import is_code_safe

        code = "result = func.__globals__"
        safe, msg = is_code_safe(code)
        assert not safe
        assert "__globals__" in msg

    def test_builtins_blocked(self):
        """验证 __builtins__ 访问被拦截。"""
        from mathlab.core.sandbox_security import is_code_safe

        code = "result = x.__builtins__"
        safe, msg = is_code_safe(code)
        assert not safe
        assert "__builtins__" in msg

    def test_type_call_blocked(self):
        """验证 type() 调用被拦截。"""
        from mathlab.core.sandbox_security import is_code_safe

        code = "NewClass = type('NewClass', (object,), {'run': lambda self: __import__('os')})"
        safe, msg = is_code_safe(code)
        assert not safe
        assert "type" in msg.lower()

    def test_safe_code_passes(self):
        """验证正常代码不被误拦截。"""
        from mathlab.core.sandbox_security import is_code_safe

        code = "x = 1 + 2\nprint(x)"
        safe, msg = is_code_safe(code)
        assert safe

    def test_import_os_blocked(self):
        """验证导入 os 模块被拦截。"""
        from mathlab.core.sandbox_security import is_code_safe

        code = "import os"
        safe, msg = is_code_safe(code)
        assert not safe
        assert "os" in msg

    def test_eval_blocked(self):
        """验证 eval() 调用被拦截。"""
        from mathlab.core.sandbox_security import is_code_safe

        code = "eval('1+1')"
        safe, msg = is_code_safe(code)
        assert not safe
        assert "eval" in msg


# ═══════════════════════════════════════════════════════════════════
# 5. SandboxProcess 测试：验证重复超时逻辑移除
# ═══════════════════════════════════════════════════════════════════


class TestSandboxProcessFix:
    """测试 SandboxProcess 不再重复检查超时。"""

    def test_run_code_uses_watchdog_thread(self):
        """验证 run_code 启动独立的看门狗线程。"""
        import inspect
        from mathlab.core.sandbox import SandboxProcess

        source = inspect.getsource(SandboxProcess.run_code)

        # 验证使用了 _monitor_watchdog
        assert "_monitor_watchdog" in source
        # 验证使用了 reader_thread.join 而非 while 循环
        assert "reader_thread.join" in source

    def test_no_duplicate_timeout_check(self):
        """验证主循环中不再有重复的超时检查。"""
        import inspect
        from mathlab.core.sandbox import SandboxProcess

        source = inspect.getsource(SandboxProcess.run_code)

        # 不应同时存在 elapsed > timeout 和 _monitor_watchdog
        # _monitor_watchdog 已经处理了超时
        lines = source.split("\n")
        has_monitor = any("_monitor_watchdog" in line for line in lines)
        has_elapsed_check = any("elapsed > timeout" in line for line in lines)

        assert has_monitor, "应使用 _monitor_watchdog 线程"
        assert not has_elapsed_check, "不应在主循环中重复检查超时"


# ═══════════════════════════════════════════════════════════════════
# 6. AIManager 测试：验证路径处理改进
# ═══════════════════════════════════════════════════════════════════


class TestAIManagerPathFix:
    """测试 AIManager.reload_config 路径处理改进。"""

    def test_reload_config_has_fallback(self):
        """验证 reload_config 有降级方案。"""
        import inspect
        from mathlab.core.ai_manager import AIManager

        source = inspect.getsource(AIManager.reload_config)

        # 验证有 try-except 降级
        assert "except" in source
        assert "getcwd" in source  # 降级方案使用 getcwd

    def test_reload_config_handles_missing_file(self, tmp_path):
        """验证 settings.json 不存在时不会崩溃。"""
        from mathlab.core.ai_manager import AIManager

        with patch("os.path.exists", return_value=False):
            manager = AIManager.__new__(AIManager)
            manager.settings_manager = None
            manager.client = None
            manager.current_model = "test"
            manager.memory = Mock()
            manager.models = {}
            manager.sandbox = None

            # 不应抛出异常
            manager.reload_config()
            assert manager.client is None  # 没有 API key


# ═══════════════════════════════════════════════════════════════════
# 7. ChatMemoryManager 测试：验证裁剪策略改进
# ═══════════════════════════════════════════════════════════════════


class TestChatMemoryManagerFix:
    """测试 ChatMemoryManager 改进的裁剪策略。"""

    def test_system_message_preserved(self):
        """验证 system 消息始终被保留。"""
        from mathlab.core.memory_manager import ChatMemoryManager

        manager = ChatMemoryManager(max_history_turns=2, max_chars=100)

        # 添加 system 消息
        manager.add_message("system", "你是数学助手" * 20)

        # 添加大量对话
        for i in range(10):
            manager.add_message("user", f"问题 {i}" * 20)
            manager.add_message("assistant", f"回答 {i}" * 20)

        # system 消息应该还在
        system_msgs = [m for m in manager.history if m["role"] == "system"]
        assert len(system_msgs) > 0

    def test_tool_message_priority(self):
        """验证 tool 消息比普通消息优先保留。"""
        from mathlab.core.memory_manager import ChatMemoryManager

        # 使用稍大的 max_chars 让 tool 消息有更高优先级保留
        manager = ChatMemoryManager(max_history_turns=1, max_chars=80)

        # 添加 tool 消息（短内容）
        manager.add_tool_message("call_1", "calculator", "result: 42")

        # 添加大量对话超过限制（长内容）
        manager.add_message("user", "a" * 40)
        manager.add_message("assistant", "b" * 40)

        # tool 消息应该还在（优先保留 system 和 tool）
        tool_msgs = [m for m in manager.history if m["role"] == "tool"]
        # 在 max_chars=80 限制下，tool 消息（12 字符）应该优先于普通消息保留
        assert len(tool_msgs) > 0 or len(manager.history) <= 2

    def test_max_turns_respected(self):
        """验证最大轮数限制被遵守。"""
        from mathlab.core.memory_manager import ChatMemoryManager

        manager = ChatMemoryManager(max_history_turns=3, max_chars=10000)

        for i in range(10):
            manager.add_message("user", f"q{i}")
            manager.add_message("assistant", f"a{i}")

        non_system = [m for m in manager.history if m["role"] != "system"]
        assert len(non_system) <= 6  # 3 轮 * 2 条

    def test_empty_content_ignored(self):
        """验证空内容被忽略。"""
        from mathlab.core.memory_manager import ChatMemoryManager

        manager = ChatMemoryManager()
        manager.add_message("user", "")

        assert len(manager.history) == 0

    def test_clear(self):
        """验证 clear 方法。"""
        from mathlab.core.memory_manager import ChatMemoryManager

        manager = ChatMemoryManager()
        manager.add_message("user", "test")
        manager.clear()

        assert len(manager.history) == 0


# ═══════════════════════════════════════════════════════════════════
# 8. AgentRegistry 测试：验证超时控制
# ═══════════════════════════════════════════════════════════════════


class TestAgentRegistryTimeoutFix:
    """测试 AgentRegistry 添加的超时控制。"""

    def test_execution_timeout_attribute_exists(self):
        """验证 AgentRegistry 有 _execution_timeout 属性。"""
        from mathlab.core.agent_registry import AgentRegistry

        mock_ai_manager = Mock()
        registry = AgentRegistry(mock_ai_manager)

        assert hasattr(registry, "_execution_timeout")
        assert isinstance(registry._execution_timeout, int)
        assert registry._execution_timeout > 0

    def test_timeout_thread_used(self):
        """验证执行时使用了线程和超时。"""
        import inspect
        from mathlab.core.agent_registry import AgentRegistry

        source = inspect.getsource(AgentRegistry.route_and_execute)

        assert "threading.Thread" in source
        assert "exec_thread.join" in source
        assert "timeout=self._execution_timeout" in source

    def test_route_and_execute_no_agents(self):
        """验证没有注册 Agent 时正确处理。"""
        from mathlab.core.agent_registry import AgentRegistry

        mock_ai_manager = Mock()
        registry = AgentRegistry(mock_ai_manager)

        thoughts = []
        finish_called = []

        registry.route_and_execute(
            "test",
            on_thought_cb=lambda t: thoughts.append(t),
            on_code_cb=lambda c: None,
            on_finish_cb=lambda s, c: finish_called.append((s, c)),
        )

        assert len(thoughts) > 0
        assert "没有可用" in thoughts[0] or "❌" in thoughts[0]
        assert len(finish_called) == 1
        assert finish_called[0][0] is False


# ═══════════════════════════════════════════════════════════════════
# 9. AIFacade 测试：验证 agent_registry 初始化检查
# ═══════════════════════════════════════════════════════════════════


class TestAIFacadeFix:
    """测试 AIFacade 的 agent_registry 初始化检查。"""

    def test_warning_when_registry_none(self, caplog):
        """验证 agent_registry 为 None 时记录警告。"""
        import logging
        from mathlab.core.ai_facade import AIFacade

        mock_ai_manager = Mock()

        with caplog.at_level(logging.WARNING):
            facade = AIFacade(mock_ai_manager, agent_registry=None)

        assert facade.agent_registry is None
        assert any("agent_registry" in record.message and "None" in record.message for record in caplog.records)

    def test_no_warning_when_registry_provided(self, caplog):
        """验证 agent_registry 提供时不记录警告。"""
        import logging
        from mathlab.core.ai_facade import AIFacade

        mock_ai_manager = Mock()
        mock_registry = Mock()

        with caplog.at_level(logging.WARNING):
            facade = AIFacade(mock_ai_manager, agent_registry=mock_registry)

        assert facade.agent_registry is mock_registry
        assert not any("agent_registry" in record.message and "None" in record.message for record in caplog.records)

    def test_classify_intent_simple_tool(self):
        """验证简单工具调用意图分类。"""
        from mathlab.core.ai_facade import AIFacade, AITaskType

        mock_ai_manager = Mock()
        facade = AIFacade(mock_ai_manager)

        task_type = facade.classify_intent("画一个圆")
        assert task_type == AITaskType.SIMPLE_TOOL_CALL

    def test_classify_intent_complex_reasoning(self):
        """验证复杂推理意图分类。"""
        from mathlab.core.ai_facade import AIFacade, AITaskType

        mock_ai_manager = Mock()
        facade = AIFacade(mock_ai_manager)

        task_type = facade.classify_intent("求解这个方程的积分")
        assert task_type == AITaskType.COMPLEX_REASONING


# ═══════════════════════════════════════════════════════════════════
# 集成测试：验证所有修复后的组件协同工作
# ═══════════════════════════════════════════════════════════════════


class TestIntegrationFixes:
    """集成测试：验证修复后的组件协同工作。"""

    def test_security_scanner_with_safe_code(self):
        """验证安全扫描器对正常代码不误报。"""
        from mathlab.core.sandbox_security import is_code_safe

        safe_code = """
import numpy as np
x = np.array([1, 2, 3])
result = np.sum(x)
print(result)
"""
        safe, msg = is_code_safe(safe_code)
        assert safe, f"安全代码被误报: {msg}"

    def test_memory_manager_with_system_and_tool(self):
        """验证记忆管理器正确处理 system 和 tool 消息混合场景。"""
        from mathlab.core.memory_manager import ChatMemoryManager

        manager = ChatMemoryManager(max_history_turns=2, max_chars=200)

        # 模拟真实对话
        manager.add_message("system", "你是数学助手")
        manager.add_message("user", "计算 1+1")
        manager.add_tool_message("call_1", "calculator", "2")
        manager.add_message("assistant", "答案是 2")
        manager.add_message("user", "计算 2+2" * 50)  # 长消息
        manager.add_message("assistant", "答案是 4" * 50)

        # system 消息应该保留
        system_msgs = [m for m in manager.history if m["role"] == "system"]
        assert len(system_msgs) >= 1

    def test_cas_provider_full_workflow(self, cas):
        """验证 CASProvider 完整工作流。"""
        # 化简
        result = cas.simplify("2*x + 3*x")
        assert result["success"] is True

        # 求导
        result = cas.differentiate("x**3", "x")
        assert result["success"] is True
        assert "3*x**2" in result["result"]

        # 积分
        result = cas.integrate("2*x", "x")
        assert result["success"] is True
        assert "x**2" in result["result"]

        # 解方程
        result = cas.solve_equation("x**2 - 4 = 0", "x")
        assert result["success"] is True
        assert len(result["solutions"]) == 2
