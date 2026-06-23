import json
import sys

def render_chart(options: dict):
    """
    沙箱内调用的桥接函数。
    它将 Python 字典转为 JSON，并包装在特殊的边界符中打印到 stdout。
    主进程的沙箱看门狗会拦截这段字符串，而不会把它当作普通的 log 显示。
    """
    try:
        # 确保 numpy array 等特殊类型能被序列化（如果需要，可添加自定义编码器）
        payload = json.dumps(options, ensure_ascii=False)
        
        # 打印魔术边界符
        print(f"\n__ECHARTS_IPC_START__\n{payload}\n__ECHARTS_IPC_END__\n")
        
        # 强制刷新缓冲区，确保主进程立刻收到
        sys.stdout.flush()
        
    except Exception as e:
        print(f"ECharts 序列化失败: {e}", file=sys.stderr)
