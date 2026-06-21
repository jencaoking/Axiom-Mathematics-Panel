"""
测试动态函数探索器功能 (Testing Dynamic Function Explorer)
"""
import sys
import os
import pytest

# 添加 mathlab 目录到路径
mathlab_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, mathlab_dir)

from ui.function_explorer_panel import FunctionExplorerPanel


def test_parameter_extraction(qtbot):
    """测试参数提取功能"""
    panel = FunctionExplorerPanel()
    qtbot.addWidget(panel)  # 由 qtbot 接管生命周期，防止回收时 core dump
    
    test_cases = [
        ("A*sin(omega*x + phi)", ["A", "omega", "phi"]),
        ("a*x^2 + b*x + c", ["a", "b", "c"]),
    ]
    
    for expr, expected in test_cases:
        params = panel._extract_parameters(expr)
        assert set(params) == set(expected), f"表达式 {expr} 参数提取失败"


def test_ui_creation(qtbot):
    """Test UI creation and basic widget properties"""
    # 1. 实例化组件
    panel = FunctionExplorerPanel()

    # 2. 向 qtbot 注册组件，确保安全销毁 C++ 对象
    qtbot.addWidget(panel)

    # 断言基本 UI 属性
    assert panel.windowTitle() is not None
    assert panel.minimumWidth() >= 0
