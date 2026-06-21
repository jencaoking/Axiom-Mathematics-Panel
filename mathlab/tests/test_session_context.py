"""
测试会话上下文传递功能
验证 REPL 在会话模式下能否正确实现变量持久化
"""
import sys
import os
import importlib.util

# 直接加载 python_repl 模块（绕过 mathlab.__init__.py）
core_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core')
sandbox_spec = importlib.util.spec_from_file_location("sandbox", os.path.join(core_path, "sandbox.py"))
sandbox_module = importlib.util.module_from_spec(sandbox_spec)
sys.modules['sandbox'] = sandbox_module  # 注册到 sys.modules
sandbox_spec.loader.exec_module(sandbox_module)

# 现在可以加载 python_repl
repl_spec = importlib.util.spec_from_file_location("python_repl", os.path.join(core_path, "python_repl.py"))
python_repl_module = importlib.util.module_from_spec(repl_spec)
repl_spec.loader.exec_module(python_repl_module)

PythonREPL = python_repl_module.PythonREPL


def test_session_mode_variable_persistence():
    """测试会话模式下的变量持久化"""
    print("=" * 70)
    print("测试 1: 会话模式 - 变量持久化")
    print("=" * 70)
    
    repl = PythonREPL(session_mode=True)  # 启用会话模式
    
    # 第一次执行：定义变量
    print("\n步骤 1: 执行 'x = 42'")
    result1 = repl.execute('x = 42')
    print(f"  成功: {result1['success']}")
    print(f"  输出: {result1['output'] if result1['output'] else '(无输出)'}")
    assert result1['success'], "第一次执行应该成功"
    
    # 第二次执行：使用之前定义的变量
    print("\n步骤 2: 执行 'print(x * 2)'")
    result2 = repl.execute('print(x * 2)')
    print(f"  成功: {result2['success']}")
    print(f"  输出: {result2['output']}")
    assert result2['success'], "第二次执行应该成功（变量 x 应该存在）"
    assert '84' in result2['output'], "应该输出 84（42 * 2）"
    
    # 第三次执行：定义函数并使用
    print("\n步骤 3: 执行 'def double(n): return n * 2'")
    result3 = repl.execute('def double(n): return n * 2')
    print(f"  成功: {result3['success']}")
    assert result3['success'], "函数定义应该成功"
    
    print("\n步骤 4: 执行 'print(double(x))'")
    result4 = repl.execute('print(double(x))')
    print(f"  成功: {result4['success']}")
    print(f"  输出: {result4['output']}")
    assert result4['success'], "函数调用应该成功"
    assert '84' in result4['output'], "应该输出 84（double(42)）"
    
    print("\n✅ 测试通过 - 会话模式下变量和函数都正确持久化\n")


def test_isolation_mode_no_persistence():
    """测试隔离模式下的完全隔离"""
    print("=" * 70)
    print("测试 2: 隔离模式 - 完全隔离（无变量持久化）")
    print("=" * 70)
    
    repl = PythonREPL(session_mode=False)  # 禁用会话模式（隔离模式）
    
    # 第一次执行：定义变量
    print("\n步骤 1: 执行 'y = 100'")
    result1 = repl.execute('y = 100')
    print(f"  成功: {result1['success']}")
    assert result1['success'], "第一次执行应该成功"
    
    # 第二次执行：尝试使用之前定义的变量（应该失败）
    print("\n步骤 2: 执行 'print(y)'")
    result2 = repl.execute('print(y)')
    print(f"  成功: {result2['success']}")
    print(f"  错误: {result2['error']}")
    assert not result2['success'], "隔离模式下第二次执行应该失败（变量 y 不存在）"
    assert 'name' in result2['error'].lower(), "应该是 NameError"
    
    print("\n✅ 测试通过 - 隔离模式下每次执行都是独立环境\n")


def test_dynamic_mode_switching():
    """测试动态切换会话/隔离模式"""
    print("=" * 70)
    print("测试 3: 动态模式切换")
    print("=" * 70)
    
    repl = PythonREPL(session_mode=True)  # 初始为会话模式
    
    # 在会话模式下定义变量
    print("\n步骤 1: [会话模式] 执行 'z = 999'")
    result1 = repl.execute('z = 999')
    print(f"  成功: {result1['success']}")
    assert result1['success']
    
    print("\n步骤 2: [会话模式] 执行 'print(z)'")
    result2 = repl.execute('print(z)')
    print(f"  成功: {result2['success']}")
    print(f"  输出: {result2['output']}")
    assert result2['success'] and '999' in result2['output']
    
    # 切换到隔离模式
    print("\n步骤 3: 切换到隔离模式")
    repl.set_session_mode(False)
    print(f"  当前模式: {'会话模式' if repl._session_mode else '隔离模式'}")
    
    # 在隔离模式下尝试访问变量（应该失败）
    print("\n步骤 4: [隔离模式] 执行 'print(z)'")
    result3 = repl.execute('print(z)')
    print(f"  成功: {result3['success']}")
    print(f"  错误: {result3['error']}")
    assert not result3['success'], "隔离模式下应该无法访问之前的变量"
    
    # 切换回会话模式
    print("\n步骤 5: 切换回会话模式")
    repl.set_session_mode(True)
    
    # 注意：切换回会话模式后，之前的上下文已被清空，所以变量 z 也不存在了
    print("\n步骤 6: [会话模式] 执行 'print(z)'")
    result4 = repl.execute('print(z)')
    print(f"  成功: {result4['success']}")
    print(f"  错误: {result4['error']}")
    assert not result4['success'], "切换模式后上下文已清空，变量 z 不存在"
    
    print("\n✅ 测试通过 - 动态模式切换正常工作\n")


def test_clear_session():
    """测试清空会话上下文"""
    print("=" * 70)
    print("测试 4: 清空会话上下文")
    print("=" * 70)
    
    repl = PythonREPL(session_mode=True)
    
    # 定义一些变量
    print("\n步骤 1: 执行 'a = 1; b = 2; c = 3'")
    repl.execute('a = 1; b = 2; c = 3')
    print(f"  会话上下文长度: {repl.get_session_context_length()}")
    
    print("\n步骤 2: 执行 'print(a + b + c)'")
    result2 = repl.execute('print(a + b + c)')
    print(f"  输出: {result2['output']}")
    assert '6' in result2['output']
    
    # 清空会话
    print("\n步骤 3: 清空会话上下文")
    repl.clear_session()
    print(f"  会话上下文长度: {repl.get_session_context_length()}")
    assert repl.get_session_context_length() == 0
    
    # 尝试访问之前的变量（应该失败）
    print("\n步骤 4: 执行 'print(a)'")
    result4 = repl.execute('print(a)')
    print(f"  成功: {result4['success']}")
    print(f"  错误: {result4['error']}")
    assert not result4['success'], "清空会话后变量应该不存在"
    
    print("\n✅ 测试通过 - 清空会话上下文功能正常\n")


def test_complex_math_operations():
    """测试复杂数学运算的会话持久化"""
    print("=" * 70)
    print("测试 5: 复杂数学运算会话持久化")
    print("=" * 70)
    
    repl = PythonREPL(session_mode=True)
    
    # 定义列表
    print("\n步骤 1: 执行 'numbers = [1, 2, 3, 4, 5]'")
    result1 = repl.execute('numbers = [1, 2, 3, 4, 5]')
    assert result1['success']
    
    # 计算总和
    print("\n步骤 2: 执行 'total = sum(numbers)'")
    result2 = repl.execute('total = sum(numbers)')
    assert result2['success']
    
    # 计算平均值
    print("\n步骤 3: 执行 'average = total / len(numbers)'")
    result3 = repl.execute('average = total / len(numbers)')
    assert result3['success']
    
    # 输出结果
    print("\n步骤 4: 执行 'print(f\"Sum: {total}, Average: {average}\")'")
    result4 = repl.execute('print(f"Sum: {total}, Average: {average}")')
    print(f"  输出: {result4['output']}")
    assert result4['success']
    assert 'Sum: 15' in result4['output']
    assert 'Average: 3.0' in result4['output']
    
    print("\n✅ 测试通过 - 复杂数学运算会话持久化正常\n")


if __name__ == '__main__':
    print("\n🚀 开始会话上下文传递功能测试\n")
    
    try:
        test_session_mode_variable_persistence()
        test_isolation_mode_no_persistence()
        test_dynamic_mode_switching()
        test_clear_session()
        test_complex_math_operations()
        
        print("\n" + "=" * 70)
        print("✅ 所有测试通过！会话上下文传递功能工作正常")
        print("=" * 70)
        print("\n💡 提示:")
        print("  - 会话模式 (session_mode=True): 类似 Jupyter，变量持久化")
        print("  - 隔离模式 (session_mode=False): 每次执行独立，更安全")
        print("  - 使用 set_session_mode() 动态切换模式")
        print("  - 使用 clear_session() 清空会话上下文")
        print("=" * 70 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
