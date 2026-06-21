"""
快速验证沙箱安全加固的核心功能
"""
import sys
import os

# 确保可以导入 core 模块（绕过 mathlab.__init__.py）
core_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core')
sys.path.insert(0, core_path)

# 直接导入 sandbox 模块
import sandbox

def test_normal_execution():
    """测试正常代码执行"""
    print("=" * 60)
    print("测试 1: 正常代码执行")
    print("=" * 60)
    
    sandbox_inst = sandbox.SandboxProcess()
    result = sandbox_inst.run_code("print('Hello World'); x = [1, 2, 3]; print(x)")
    
    print(f"成功: {result['success']}")
    print(f"输出: {result['output']}")
    print(f"错误: {result['error']}")
    
    assert result['success'] == True, "正常代码应该执行成功"
    assert 'Hello World' in result['output'], "应该捕获到输出"
    assert '[1, 2, 3]' in result['output'], "应该捕获到列表输出"
    print("✓ 测试通过\n")


def test_timeout_protection():
    """测试超时保护机制"""
    print("=" * 60)
    print("测试 2: 死循环超时保护（预计等待 2-3 秒）")
    print("=" * 60)
    
    sandbox_inst = sandbox.SandboxProcess()
    result = sandbox_inst.run_code("while True: pass", timeout=2)
    
    print(f"成功: {result['success']}")
    print(f"错误信息: {result['error']}")
    
    assert result['success'] == False, "死循环应该被终止"
    assert len(result['error']) > 0, "应该有错误信息"
    print("✓ 测试通过 - 看门狗成功终止了死循环\n")


def test_memory_protection():
    """测试内存限制（如果安装了 psutil）"""
    print("=" * 60)
    print("测试 3: 内存溢出保护（预计等待 5-10 秒）")
    print("=" * 60)
    
    try:
        import psutil
        print("检测到 psutil，将进行内存监控测试")
        
        sandbox_inst = sandbox.SandboxProcess()
        sandbox_inst.max_memory_mb = 50  # 降低阈值以便快速测试
        code = "arr = []\nwhile True:\n    arr.append('X' * 1000000)"
        result = sandbox_inst.run_code(code, timeout=10)
        
        print(f"成功: {result['success']}")
        print(f"错误信息: {result['error']}")
        
        assert result['success'] == False, "内存溢出应该被阻止"
        assert 'Memory limit' in result['error'] or 'timed out' in result['error'].lower(), \
            "应该触发内存限制或超时"
        print("✓ 测试通过 - 看门狗成功阻止了内存溢出\n")
        
    except ImportError:
        print("未安装 psutil，跳过内存监控测试")
        print("提示: 运行 pip install psutil 以启用内存保护\n")


def test_sandbox_isolation():
    """测试沙箱隔离性"""
    print("=" * 60)
    print("测试 4: 沙箱隔离性验证")
    print("=" * 60)
    
    # 由于 python_repl 使用相对导入，我们需要通过 mathlab.core 路径导入
    # 先将 mathlab 目录加入 sys.path
    mathlab_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if mathlab_path not in sys.path:
        sys.path.insert(0, mathlab_path)
    
    try:
        from mathlab.core.python_repl import PythonREPL
        repl = PythonREPL(session_mode=False)
    except ImportError as e:
        print(f"无法导入 PythonREPL: {e}")
        print("跳过此测试（需要完整的环境依赖）\n")
        return
    
    # 第一次执行：定义变量
    result1 = repl.execute('a = 42')
    print(f"第一次执行 (a = 42): 成功={result1['success']}")
    
    # 第二次执行：尝试访问之前定义的变量（应该失败）
    result2 = repl.execute('print(a)')
    print(f"第二次执行 (print(a)): 成功={result2['success']}")
    print(f"错误信息: {result2['error']}")
    
    assert result1['success'] == True, "第一次执行应该成功"
    assert result2['success'] == False, "第二次执行应该失败（变量不持久化）"
    print("✓ 测试通过 - 每次执行都是独立沙箱环境\n")


if __name__ == '__main__':
    print("\n🚀 开始沙箱安全加固验证测试\n")
    
    try:
        test_normal_execution()
        test_timeout_protection()
        test_memory_protection()
        test_sandbox_isolation()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！沙箱安全加固系统工作正常")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
