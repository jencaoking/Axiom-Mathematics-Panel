"""
测试动态函数探索器功能
"""
import sys
import os

# 添加mathlab目录到路径
mathlab_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, mathlab_dir)

from PySide6.QtWidgets import QApplication
from ui.function_explorer_panel import FunctionExplorerPanel

def test_parameter_extraction():
    """测试参数提取功能"""
    print("测试1: 参数提取")
    print("=" * 60)
    
    panel = FunctionExplorerPanel()
    
    test_cases = [
        ("A*sin(omega*x + phi)", ["A", "omega", "phi"]),
        ("a*x^2 + b*x + c", ["a", "b", "c"]),
        ("x^2", []),
        ("sin(x)", []),
        ("a*exp(b*x)", ["a", "b"]),
    ]
    
    for expr, expected in test_cases:
        params = panel._extract_parameters(expr)
        status = "✓" if set(params) == set(expected) else "✗"
        print(f"{status} 表达式: {expr}")
        print(f"   期望: {expected}")
        print(f"   实际: {params}")
        print()

def test_ui_creation():
    """测试UI创建"""
    print("\n测试2: UI创建")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    panel = FunctionExplorerPanel()
    
    print("✓ 面板创建成功")
    print(f"  标题: {panel.windowTitle()}")
    print(f"  最小宽度: {panel.minimumWidth()}")
    print()

if __name__ == '__main__':
    test_parameter_extraction()
    test_ui_creation()
    print("\n所有测试完成!")
