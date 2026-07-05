from PySide6.QtCore import QObject, Signal, QThread
import traceback

class AgentTaskWorker(QThread):
    def __init__(self, agent_registry, user_prompt, thought_cb, code_cb, finish_cb, observation_cb, parent=None):
        super().__init__(parent)
        self.agent_registry = agent_registry
        self.user_prompt = user_prompt
        self.thought_cb = thought_cb
        self.code_cb = code_cb
        self.finish_cb = finish_cb
        self.observation_cb = observation_cb

    def run(self):
        try:
            # 兼容当前的参数列表，保留 observation_cb 用于将来在 agent 内部进行结果回调
            self.agent_registry.route_and_execute(
                self.user_prompt, 
                self.thought_cb, 
                self.code_cb, 
                self.finish_cb
            )
        except Exception as e:
            error_msg = f"Task execution failed: {str(e)}\n{traceback.format_exc()}"
            self.finish_cb(False, error_msg)

class AgentUIBridge(QObject):
    """
    专门负责将后台 MathAgent 的生命周期事件，安全地转发到前端 UI 线程
    """
    # 定义强类型的跨线程信号
    thought_emitted = Signal(str)           # 触发控制台打印 Thought
    observation_emitted = Signal(str, bool) # 触发控制台打印沙箱结果 (文本, 是否报错)
    code_generated = Signal(str)            # 触发 Monaco 编辑器打字
    task_finished = Signal(bool, str)       # 触发结束动画

    def __init__(self, agent_registry, parent=None):
        super().__init__(parent)
        self.agent_registry = agent_registry
        self._current_worker = None

    def run_task_in_background(self, user_prompt):
        """将任务抛入后台线程执行，并通过回调发射信号"""
        if self._current_worker is not None and self._current_worker.isRunning():
            return  # 防止重入，丢弃并发请求
            
        def _thought_cb(text):
            # 将终端打印转化为 UI 信号
            self.thought_emitted.emit(text)
            
        def _code_cb(code):
            self.code_generated.emit(code)
            
        def _finish_cb(success, final_content):
            self.task_finished.emit(success, final_content)

        def _observation_cb(text, is_error):
            # 完善 _observation_cb 支持，彻底接通观察回调
            self.observation_emitted.emit(text, is_error)

        # 启动 QThread 运行大模型闭环，实现生命周期托管与异常兜底
        self._current_worker = AgentTaskWorker(
            self.agent_registry, 
            user_prompt, 
            _thought_cb, 
            _code_cb, 
            _finish_cb,
            _observation_cb,
            self
        )
        self._current_worker.finished.connect(self._current_worker.deleteLater)
        self._current_worker.start()
