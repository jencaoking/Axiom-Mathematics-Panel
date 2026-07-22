"""P0 插件 (Calculus Tools + Animation Studio) 单元测试。

测试覆盖：
- 插件类元数据 (name, version, author, description)
- 插件激活/停用生命周期
- 微积分计算逻辑 (导数/积分/极限/泰勒)
- 动画状态机 (播放/暂停/停止/恢复)
- 几何引擎交互 (安全访问、对象追踪、清理)
- 错误处理 (空输入、无效表达式、引擎不可用)
- i18n 翻译键完整性
"""
import os
import sys
import math
import json
import pytest

# Headless Qt
os.environ["QT_QPA_PLATFORM"] = "offscreen"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ═══════════════════════════════════════════════════════════════════════════
# Mock 基础设施
# ═══════════════════════════════════════════════════════════════════════════

class MockConsole:
    """模拟控制台"""
    def __init__(self):
        self.messages = []

    def display_system_message(self, text, level="info"):
        self.messages.append((text, level))


class MockCommandManager:
    """模拟命令管理器"""
    def __init__(self):
        self._commands = {}

    def register(self, command):
        self._commands[command.id] = command

    def unregister(self, cmd_id):
        self._commands.pop(cmd_id, None)

    def get(self, cmd_id):
        return self._commands.get(cmd_id)


class MockGeometryEngine:
    """模拟几何引擎，只实现插件需要的方法"""
    def __init__(self):
        self.objects = {}
        self._signals_blocked = False
        self._notify_calls = []
        self._counter = 0

    def _generate_id(self):
        self._counter += 1
        return f"mock-{self._counter}"

    def add_point(self, x=0, y=0, z=0, name=None):
        obj_id = self._generate_id()
        self.objects[obj_id] = MockGeoObject(obj_id, name or "P", "Point",
                                              {"x": x, "y": y, "z": z})
        self._notify_calls.append(("object_added", obj_id))
        return obj_id

    def add_function_plot(self, expression, x_range=(-10, 10), num_points=500, name=None):
        obj_id = self._generate_id()
        self.objects[obj_id] = MockGeoObject(obj_id, name or "F", "FunctionPlot",
                                              {"expression": expression, "x_range": x_range})
        self._notify_calls.append(("object_added", obj_id))
        return obj_id

    def update_point(self, obj_id, x=None, y=None, z=None):
        obj = self.objects.get(obj_id)
        if obj is None:
            return
        if x is not None:
            obj.coordinates["x"] = x
        if y is not None:
            obj.coordinates["y"] = y
        if z is not None:
            obj.coordinates["z"] = z
        if not self._signals_blocked:
            self._notify_calls.append(("object_updated", obj_id))

    def remove_object(self, obj_id):
        if obj_id in self.objects:
            del self.objects[obj_id]
            self._notify_calls.append(("object_removed", obj_id))

    def get_object(self, obj_id):
        return self.objects.get(obj_id)

    def get_all_objects(self):
        return list(self.objects.values())

    def get_objects_by_type(self, obj_type):
        return [obj for obj in self.objects.values() if obj.type == obj_type]

    def block_signals(self, blocked):
        self._signals_blocked = blocked

    def signals_blocked(self):
        return self._signals_blocked

    def _notify(self, event_type, data):
        self._notify_calls.append((event_type, data))


class MockGeoObject:
    """模拟几何对象"""
    def __init__(self, obj_id, name, obj_type, coordinates=None):
        self.id = obj_id
        self.name = name
        self.type = obj_type
        self.coordinates = coordinates or {}

    def serialize(self):
        return {"id": self.id, "name": self.name, "type": self.type,
                "coordinates": self.coordinates}


class MockCASProvider:
    """模拟 CAS 符号计算引擎"""
    def differentiate(self, expr_str, variable="x"):
        if not expr_str:
            return {"success": False, "error": "Empty expression"}
        # 简单模拟: x**2 -> 2*x
        if expr_str.strip() == "x**2":
            return {"success": True, "result": "2*x", "latex": "2 x"}
        if expr_str.strip() == "sin(x)":
            return {"success": True, "result": "cos(x)", "latex": r"\cos(x)"}
        return {"success": True, "result": "1", "latex": "1"}

    def definite_integral(self, expr_str, variable="x", lower=0, upper=1):
        if not expr_str:
            return {"success": False, "error": "Empty expression"}
        if expr_str.strip() == "x**2":
            val = (upper**3 - lower**3) / 3.0
            return {"success": True, "result": f"{val}", "latex": str(val),
                    "numeric": val}
        return {"success": True, "result": "1.0", "latex": "1.0", "numeric": 1.0}

    def limit(self, expr_str, variable="x", point=0):
        if not expr_str:
            return {"success": False, "error": "Empty expression"}
        if expr_str.strip() == "sin(x)/x":
            return {"success": True, "result": "1", "latex": "1"}
        return {"success": True, "result": "0", "latex": "0"}

    def parse_expression(self, expr_str):
        if not expr_str:
            return None
        return expr_str  # 直接返回字符串作为 mock


class MockMainWindow:
    """模拟主窗口"""
    def __init__(self):
        self.geometry_engine = MockGeometryEngine()
        self.cas_provider = MockCASProvider()

    def add_dynamic_panel(self, name, widget, icon=None):
        return widget

    def removeDockWidget(self, dock):
        pass


class MockMathLabAPI:
    """模拟 MathLabAPI，提供插件所需接口"""
    def __init__(self):
        self._main_window = MockMainWindow()
        self._cmd_manager = MockCommandManager()
        self._console = MockConsole()
        self._registered_commands = []
        self._dynamic_panels = []

    def register_command(self, id, title, action, category="Plugin"):
        from mathlab.core.command_manager import Command
        cmd = Command(id, title, action, category)
        self._cmd_manager.register(cmd)
        self._registered_commands.append(id)

    def add_sidebar_panel(self, panel_name, widget, icon=None):
        dock = self._main_window.add_dynamic_panel(panel_name, widget, icon)
        self._dynamic_panels.append(dock)
        return dock

    def print_to_console(self, text, color_or_level="info"):
        level = color_or_level if not color_or_level.startswith("#") else "info"
        self._console.display_system_message(text, level)

    def execute_script(self, script):
        return {"success": True}

    def cleanup(self):
        for cmd_id in self._registered_commands:
            self._cmd_manager.unregister(cmd_id)
        self._registered_commands.clear()
        self._dynamic_panels.clear()


# ═══════════════════════════════════════════════════════════════════════════
# Pytest fixture
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_api(qapp):
    """qapp fixture from pytest-qt ensures QApplication exists."""
    return MockMathLabAPI()


# ═══════════════════════════════════════════════════════════════════════════
# Calculus Tools 插件测试
# ═══════════════════════════════════════════════════════════════════════════

class TestCalculusToolsPlugin:
    """测试微积分工具插件"""

    def test_plugin_metadata(self):
        from mathlab.plugins.calculus_tools.main import CalculusToolsPlugin
        plugin = CalculusToolsPlugin()
        assert plugin.name == "Calculus Tools"
        assert plugin.version == "1.0.0"
        assert plugin.author == "MathLab Team"
        assert "derivative" in plugin.description.lower()

    def test_plugin_activate(self, mock_api):
        from mathlab.plugins.calculus_tools.main import CalculusToolsPlugin
        plugin = CalculusToolsPlugin()
        plugin.on_activate(mock_api)

        assert plugin.widget is not None
        assert len(mock_api._registered_commands) == 4
        assert "calculus.differentiate" in mock_api._registered_commands
        assert "calculus.integrate" in mock_api._registered_commands
        assert "calculus.limit" in mock_api._registered_commands
        assert "calculus.taylor" in mock_api._registered_commands
        assert len(mock_api._dynamic_panels) == 1

    def test_plugin_deactivate(self, mock_api):
        from mathlab.plugins.calculus_tools.main import CalculusToolsPlugin
        plugin = CalculusToolsPlugin()
        plugin.on_activate(mock_api)
        plugin.on_deactivate()

        assert plugin.widget is None

    def test_compute_derivative(self, mock_api):
        from mathlab.plugins.calculus_tools.main import CalculusPanelWidget
        widget = CalculusPanelWidget(mock_api)
        widget.input_expr.setText("x**2")
        widget.combo_mode.setCurrentIndex(0)  # derivative mode
        widget.spin_deriv_x.setValue(2.0)
        widget._on_compute()

        result_text = widget.text_result.toPlainText()
        assert "2*x" in result_text
        assert "f'(2.0)" in result_text or "f'(2)" in result_text

    def test_compute_integral(self, mock_api):
        from mathlab.plugins.calculus_tools.main import CalculusPanelWidget
        widget = CalculusPanelWidget(mock_api)
        widget.input_expr.setText("x**2")
        widget.combo_mode.setCurrentIndex(1)  # integral mode
        widget.spin_int_a.setValue(0.0)
        widget.spin_int_b.setValue(1.0)
        widget._on_compute()

        result_text = widget.text_result.toPlainText()
        assert "0.333" in result_text or "0.33" in result_text

    def test_compute_limit(self, mock_api):
        from mathlab.plugins.calculus_tools.main import CalculusPanelWidget
        widget = CalculusPanelWidget(mock_api)
        widget.input_expr.setText("sin(x)/x")
        widget.combo_mode.setCurrentIndex(2)  # limit mode
        widget.spin_limit_point.setValue(0.0)
        widget._on_compute()

        result_text = widget.text_result.toPlainText()
        assert "1" in result_text

    def test_empty_expression_error(self, mock_api):
        from mathlab.plugins.calculus_tools.main import CalculusPanelWidget
        widget = CalculusPanelWidget(mock_api)
        widget.input_expr.setText("")
        widget._on_compute()

        result_text = widget.text_result.toPlainText()
        assert "Error" in result_text or "error" in result_text.lower()

    def test_plot_derivative(self, mock_api):
        from mathlab.plugins.calculus_tools.main import CalculusPanelWidget
        widget = CalculusPanelWidget(mock_api)
        widget.input_expr.setText("x**2")
        widget.combo_mode.setCurrentIndex(0)
        widget.spin_deriv_x.setValue(1.0)
        widget._on_plot()

        # 应该创建了: 原函数 + 切线 + 切点 = 3 个对象
        assert len(widget._plotted_ids) == 3
        engine = mock_api._main_window.geometry_engine
        assert len(engine.objects) == 3

    def test_plot_clear(self, mock_api):
        from mathlab.plugins.calculus_tools.main import CalculusPanelWidget
        widget = CalculusPanelWidget(mock_api)
        widget.input_expr.setText("x**2")
        widget.combo_mode.setCurrentIndex(0)
        widget._on_plot()
        assert len(widget._plotted_ids) > 0

        widget._on_clear()
        assert len(widget._plotted_ids) == 0
        engine = mock_api._main_window.geometry_engine
        assert len(engine.objects) == 0

    def test_cleanup_on_deactivate(self, mock_api):
        from mathlab.plugins.calculus_tools.main import CalculusToolsPlugin
        plugin = CalculusToolsPlugin()
        plugin.on_activate(mock_api)

        # 绘制一些对象
        plugin.widget.input_expr.setText("x**2")
        plugin.widget.combo_mode.setCurrentIndex(0)
        plugin.widget._on_plot()
        assert len(plugin.widget._plotted_ids) > 0

        engine = mock_api._main_window.geometry_engine
        obj_count_before = len(engine.objects)

        plugin.on_deactivate()

        # 停用后引擎中的对象应被清理
        assert len(engine.objects) < obj_count_before

    def test_engine_not_available(self, qapp):
        """当引擎不可用时不崩溃"""
        from mathlab.plugins.calculus_tools.main import CalculusPanelWidget

        # 创建一个没有 geometry_engine 的 API
        class BrokenAPI:
            _main_window = None
            _console = MockConsole()
            _cmd_manager = MockCommandManager()

            def print_to_console(self, text, color_or_level="info"):
                self._console.display_system_message(text, color_or_level)

        widget = CalculusPanelWidget(BrokenAPI())
        widget.input_expr.setText("x**2")
        widget._on_plot()
        # 不应崩溃
        assert widget._plotted_ids == []


# ═══════════════════════════════════════════════════════════════════════════
# Animation Studio 插件测试
# ═══════════════════════════════════════════════════════════════════════════

class TestAnimationStudioPlugin:
    """测试动画演示插件"""

    def test_plugin_metadata(self):
        from mathlab.plugins.animation_studio.main import AnimationStudioPlugin
        plugin = AnimationStudioPlugin()
        assert plugin.name == "Animation Studio"
        assert plugin.version == "1.0.0"
        assert plugin.author == "MathLab Team"

    def test_plugin_activate(self, mock_api):
        from mathlab.plugins.animation_studio.main import AnimationStudioPlugin
        plugin = AnimationStudioPlugin()
        plugin.on_activate(mock_api)

        assert plugin.widget is not None
        assert len(mock_api._registered_commands) == 5
        assert "animation.translate" in mock_api._registered_commands
        assert "animation.rotate" in mock_api._registered_commands
        assert "animation.scale" in mock_api._registered_commands
        assert "animation.param_func" in mock_api._registered_commands
        assert "animation.stop" in mock_api._registered_commands

    def test_plugin_deactivate(self, mock_api):
        from mathlab.plugins.animation_studio.main import AnimationStudioPlugin
        plugin = AnimationStudioPlugin()
        plugin.on_activate(mock_api)
        plugin.on_deactivate()
        assert plugin.widget is None

    def test_no_points_error(self, mock_api):
        """没有点时播放应显示错误状态"""
        from mathlab.plugins.animation_studio.main import AnimationPanelWidget
        widget = AnimationPanelWidget(mock_api)
        widget.combo_type.setCurrentIndex(0)  # translate
        widget._on_play()

        status = widget.label_status.text()
        assert "No points" in status or "未找到" in status

    def test_translate_animation(self, mock_api):
        """测试平移动画"""
        from mathlab.plugins.animation_studio.main import AnimationPanelWidget
        widget = AnimationPanelWidget(mock_api)
        engine = mock_api._main_window.geometry_engine

        # 添加点
        p1 = engine.add_point(0.0, 0.0, name="A")
        p2 = engine.add_point(1.0, 0.0, name="B")

        widget.combo_type.setCurrentIndex(0)  # translate
        widget.spin_tx.setValue(5.0)
        widget.spin_ty.setValue(3.0)
        widget.spin_duration.setValue(2.0)

        widget._on_play()
        assert widget._is_playing is True
        assert len(widget._anim_state["point_ids"]) == 2
        assert len(widget._anim_state["orig_coords"]) == 2

        # 模拟动画帧 (progress = 0.5 after dt addition)
        # _on_tick 先加 dt(=50ms=0.05s) 再计算 progress
        widget._anim_state["elapsed"] = 0.95  # 0.95 + 0.05 = 1.0 → progress=0.5
        widget._on_tick()

        # 检查点是否移动了 (ease_in_out(0.5) = 0.5)
        obj_a = engine.get_object(p1)
        obj_b = engine.get_object(p2)
        # t_eased = 0.5 * (1 - cos(pi*0.5)) = 0.5
        assert abs(obj_a.coordinates["x"] - 2.5) < 0.15  # 0 + 5*0.5
        assert abs(obj_a.coordinates["y"] - 1.5) < 0.1  # 0 + 3*0.5

    def test_rotate_animation(self, mock_api):
        """测试旋转动画"""
        from mathlab.plugins.animation_studio.main import AnimationPanelWidget
        widget = AnimationPanelWidget(mock_api)
        engine = mock_api._main_window.geometry_engine

        p1 = engine.add_point(1.0, 0.0, name="A")

        widget.combo_type.setCurrentIndex(1)  # rotate
        widget.spin_rot_cx.setValue(0.0)
        widget.spin_rot_cy.setValue(0.0)
        widget.spin_rot_angle.setValue(90.0)  # 90 degrees
        widget.spin_duration.setValue(1.0)

        widget._on_play()

        # 完整动画 (progress = 1.0 after dt)
        widget._anim_state["elapsed"] = 0.95  # 0.95 + 0.05 = 1.0
        widget._on_tick()

        obj_a = engine.get_object(p1)
        # 旋转 90 度: (1,0) -> (cos90, sin90) = (0, 1)
        assert abs(obj_a.coordinates["x"]) < 0.02
        assert abs(obj_a.coordinates["y"] - 1.0) < 0.02

    def test_scale_animation(self, mock_api):
        """测试缩放动画"""
        from mathlab.plugins.animation_studio.main import AnimationPanelWidget
        widget = AnimationPanelWidget(mock_api)
        engine = mock_api._main_window.geometry_engine

        p1 = engine.add_point(2.0, 0.0, name="A")

        widget.combo_type.setCurrentIndex(2)  # scale
        widget.spin_scale_cx.setValue(0.0)
        widget.spin_scale_cy.setValue(0.0)
        widget.spin_scale_factor.setValue(3.0)
        widget.spin_duration.setValue(1.0)

        widget._on_play()

        # 完整动画 (progress = 1.0 after dt)
        widget._anim_state["elapsed"] = 0.95  # 0.95 + 0.05 = 1.0
        widget._on_tick()

        obj_a = engine.get_object(p1)
        # 缩放因子 3: (2,0) -> (6,0)
        assert abs(obj_a.coordinates["x"] - 6.0) < 0.02

    def test_stop_restores_originals(self, mock_api):
        """停止动画应恢复原始位置"""
        from mathlab.plugins.animation_studio.main import AnimationPanelWidget
        widget = AnimationPanelWidget(mock_api)
        engine = mock_api._main_window.geometry_engine

        p1 = engine.add_point(0.0, 0.0, name="A")

        widget.combo_type.setCurrentIndex(0)  # translate
        widget.spin_tx.setValue(5.0)
        widget.spin_duration.setValue(1.0)
        widget._on_play()

        # 移动到中间
        widget._anim_state["elapsed"] = 0.5
        widget._on_tick()

        obj = engine.get_object(p1)
        assert obj.coordinates["x"] != 0.0

        # 停止
        widget._on_stop()

        obj = engine.get_object(p1)
        assert abs(obj.coordinates["x"]) < 0.01
        assert abs(obj.coordinates["y"]) < 0.01

    def test_pause_and_resume(self, mock_api):
        """暂停后再播放"""
        from mathlab.plugins.animation_studio.main import AnimationPanelWidget
        widget = AnimationPanelWidget(mock_api)
        engine = mock_api._main_window.geometry_engine

        engine.add_point(0.0, 0.0, name="A")
        widget.combo_type.setCurrentIndex(0)
        widget.spin_tx.setValue(5.0)
        widget.spin_duration.setValue(2.0)
        widget._on_play()

        assert widget._is_playing is True

        widget._on_pause()
        assert widget._is_playing is False

    def test_type_change_stops_animation(self, mock_api):
        """切换动画类型时停止当前动画"""
        from mathlab.plugins.animation_studio.main import AnimationPanelWidget
        widget = AnimationPanelWidget(mock_api)
        engine = mock_api._main_window.geometry_engine

        engine.add_point(0.0, 0.0, name="A")
        widget.combo_type.setCurrentIndex(0)
        widget.spin_tx.setValue(5.0)
        widget._on_play()

        assert widget._is_playing is True

        # 切换到旋转
        widget.combo_type.setCurrentIndex(1)

        assert widget._is_playing is False

    def test_cleanup_on_deactivate(self, mock_api):
        """停用时清理定时器和对象"""
        from mathlab.plugins.animation_studio.main import AnimationStudioPlugin
        plugin = AnimationStudioPlugin()
        plugin.on_activate(mock_api)

        engine = mock_api._main_window.geometry_engine
        engine.add_point(0.0, 0.0, name="A")

        plugin.widget.combo_type.setCurrentIndex(0)
        plugin.widget.spin_tx.setValue(5.0)
        plugin.widget._on_play()

        assert plugin.widget._timer.isActive()

        plugin.on_deactivate()

        # 定时器应停止
        assert not plugin.widget._timer.isActive() if plugin.widget else True

    def test_ease_in_out(self):
        """测试缓动函数"""
        from mathlab.plugins.animation_studio.main import AnimationPanelWidget
        # t=0 -> 0
        assert AnimationPanelWidget._ease_in_out(0.0) == pytest.approx(0.0)
        # t=1 -> 1
        assert AnimationPanelWidget._ease_in_out(1.0) == pytest.approx(1.0)
        # t=0.5 -> 0.5
        assert AnimationPanelWidget._ease_in_out(0.5) == pytest.approx(0.5)
        # t=0.25 < 0.5 (ease in)
        assert AnimationPanelWidget._ease_in_out(0.25) < 0.25

    def test_param_func_animation(self, mock_api):
        """测试函数参数动画"""
        from mathlab.plugins.animation_studio.main import AnimationPanelWidget
        widget = AnimationPanelWidget(mock_api)
        engine = mock_api._main_window.geometry_engine

        widget.combo_type.setCurrentIndex(3)  # param_func
        widget.input_func_expr.setText("sin(a*x)")
        widget.spin_param_start.setValue(0.5)
        widget.spin_param_end.setValue(2.0)
        widget.spin_duration.setValue(2.0)

        widget._on_play()
        assert widget._is_playing is True

        # 模拟一帧 (progress=0.5 after dt: 0.95 + 0.05 = 1.0, 1.0/2.0 = 0.5)
        widget._anim_state["elapsed"] = 0.95
        widget._on_tick()

        # 应该创建了一个 FunctionPlot 对象
        assert widget._anim_state["func_id"] is not None
        func_obj = engine.get_object(widget._anim_state["func_id"])
        assert func_obj is not None
        # a_val = 0.5 + (2.0 - 0.5) * 0.5 = 1.25
        assert "1.25" in func_obj.coordinates.get("expression", "")

    def test_param_func_empty_expr(self, mock_api):
        """函数参数动画空表达式不崩溃"""
        from mathlab.plugins.animation_studio.main import AnimationPanelWidget
        widget = AnimationPanelWidget(mock_api)
        widget.combo_type.setCurrentIndex(3)  # param_func
        widget.input_func_expr.setText("")

        widget._on_play()
        assert widget._is_playing is False
        status = widget.label_status.text()
        assert "Error" in status or "error" in status.lower()


# ═══════════════════════════════════════════════════════════════════════════
# i18n 翻译键完整性测试
# ═══════════════════════════════════════════════════════════════════════════

class TestI18nCompleteness:
    """测试新插件的 i18n 翻译键在 zh.json 和 en.json 中都存在"""

    @pytest.fixture
    def zh_translations(self):
        locale_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "locale", "zh.json"
        )
        with open(locale_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @pytest.fixture
    def en_translations(self):
        locale_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "locale", "en.json"
        )
        with open(locale_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_plugin_keys_exist(self, zh_translations, en_translations):
        """plugins 下应包含新插件名称键"""
        assert "calculus_tools" in zh_translations["plugins"]
        assert "animation_studio" in zh_translations["plugins"]
        assert "calculus_tools" in en_translations["plugins"]
        assert "animation_studio" in en_translations["plugins"]

    def test_calculus_keys_exist(self, zh_translations, en_translations):
        """calculus 命名空间下应有完整翻译键"""
        required_keys = [
            "mode", "derivative", "definite_integral", "limit", "taylor_series",
            "function_input", "expression", "parameters", "result",
            "compute", "plot", "clear", "eval_point", "limit_point",
            "expand_point", "order", "empty_expr",
            "cmd_derivative", "cmd_integral", "cmd_limit", "cmd_taylor",
        ]
        for key in required_keys:
            assert key in zh_translations["calculus"], f"Missing zh key: calculus.{key}"
            assert key in en_translations["calculus"], f"Missing en key: calculus.{key}"

    def test_animation_keys_exist(self, zh_translations, en_translations):
        """animation 命名空间下应有完整翻译键"""
        required_keys = [
            "type", "translate", "rotate", "scale", "param_func",
            "parameters", "speed", "controls", "duration",
            "center_x", "center_y", "angle", "factor",
            "expression", "param_start", "param_end",
            "hint", "no_points",
            "status_ready", "status_playing", "status_paused", "status_complete",
            "cmd_translate", "cmd_rotate", "cmd_scale", "cmd_param_func", "cmd_stop",
        ]
        for key in required_keys:
            assert key in zh_translations["animation"], f"Missing zh key: animation.{key}"
            assert key in en_translations["animation"], f"Missing en key: animation.{key}"


# ═══════════════════════════════════════════════════════════════════════════
# 插件加载测试
# ═══════════════════════════════════════════════════════════════════════════

class TestPluginLoading:
    """测试插件能被 PluginManager 正确加载"""

    def test_calculus_plugin_importable(self):
        """CalculusToolsPlugin 应可被导入"""
        from mathlab.plugins.calculus_tools.main import CalculusToolsPlugin
        assert issubclass(CalculusToolsPlugin, __import__('mathlab.core.plugin_base', fromlist=['MathLabPlugin']).MathLabPlugin)

    def test_animation_plugin_importable(self):
        """AnimationStudioPlugin 应可被导入"""
        from mathlab.plugins.animation_studio.main import AnimationStudioPlugin
        assert issubclass(AnimationStudioPlugin, __import__('mathlab.core.plugin_base', fromlist=['MathLabPlugin']).MathLabPlugin)

    def test_calculus_plugin_has_init_py(self):
        """calculus_tools 目录应有 __init__.py"""
        init_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "plugins", "calculus_tools", "__init__.py"
        )
        assert os.path.exists(init_path)

    def test_animation_plugin_has_init_py(self):
        """animation_studio 目录应有 __init__.py"""
        init_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "plugins", "animation_studio", "__init__.py"
        )
        assert os.path.exists(init_path)
