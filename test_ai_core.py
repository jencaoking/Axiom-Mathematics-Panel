import sys
import time
from PySide6.QtCore import QCoreApplication
from mathlab.core.ai_manager import AIManager

def main():
    # 因为底层使用了 QThread 和 Signal，必须启动 Qt 的事件循环，即便没有界面
    app = QCoreApplication(sys.argv)
    
    # 初始化 AI 管理器 (请确保您在 ai_manager.py 中填入了测试 API Key)
    ai = AIManager()

    # 1. 定义回调函数
    def handle_chunk(text):
        print(text, end="", flush=True)

    def handle_finish(text=""):
        print("\n\n[对话结束]")
        # 测试第二轮对话，验证上下文记忆
        print(">>> 测试第二轮上下文记忆...")
        ai.ask_stream("我刚才问了你什么？", on_chunk=handle_chunk, on_finish=lambda t="": app.quit())

    def handle_error(err):
        print(f"\n[错误]: {err}")
        app.quit()

    # 2. 发起第一轮请求
    print(">>> 正在请求大模型...\n")
    ai.ask_stream(
        user_prompt="你好，用一句话解释什么是泰勒展开？",
        system_prompt="你是一个严谨的数学教授。",
        on_chunk=handle_chunk,
        on_finish=handle_finish,
        on_error=handle_error
    )

    # 启动事件循环
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
