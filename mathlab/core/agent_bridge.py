from PySide6.QtCore import QObject, Signal, QThread
import json

class AgentUIBridge(QObject):
    """
    专门负责将后台 MathAgent 的生命周期事件，安全地转发到前端 UI 线程
    """
    # 定义强类型的跨线程信号
    thought_emitted = Signal(str)           # 触发控制台打印 Thought
    observation_emitted = Signal(str, bool) # 触发控制台打印沙箱结果 (文本, 是否报错)
    code_generated = Signal(str)            # 触发 Monaco 编辑器打字
    task_finished = Signal(bool, str)       # 触发结束动画

    def __init__(self, agent_instance, parent=None):
        super().__init__(parent)
        self.agent = agent_instance

    def run_task_in_background(self, user_prompt):
        """将任务抛入后台线程执行，并通过回调发射信号"""
        def _thought_cb(text):
            # 将终端打印转化为 UI 信号
            self.thought_emitted.emit(text)
            
        def _code_cb(code):
            self.code_generated.emit(code)
            
        def _finish_cb(success, final_content):
            self.task_finished.emit(success, final_content)

        # 重写 Agent 的底层沙箱观测拦截，以便发送 observation 信号
        # (这里假设你在 MathAgent.solve_problem 中可以抛出 observation)
        
        # 启动守护线程运行大模型闭环
        import threading
        threading.Thread(
            target=self.agent.solve_problem,
            args=(user_prompt, _thought_cb, _code_cb, _finish_cb),
            daemon=True
        ).start()
