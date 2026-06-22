from mathlab.utils.logger import get_logger

logger = get_logger(__name__)

class ChatMemoryManager:
    """
    滑动窗口记忆管理器：防止多轮对话撑爆 Token 限制并节省 API 费用
    """
    def __init__(self, max_history_turns=10, max_chars=8000):
        self.max_history_turns = max_history_turns
        self.max_chars = max_chars
        self.history = []

    def add_message(self, role: str, content: str):
        """添加一条消息并自动修剪记忆"""
        if not content:
            return
        self.history.append({"role": role, "content": content})
        self._prune_memory()

    def add_tool_message(self, tool_call_id: str, name: str, content: str):
        """专门记录工具调用的结果，保持上下文一致性"""
        self.history.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": name,
            "content": content
        })
        self._prune_memory()

    def _prune_memory(self):
        """核心裁剪策略"""
        # 1. 按轮数裁剪（保留最新的 N 轮）
        max_messages = self.max_history_turns * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]
            
        # 2. 按字符数粗略估算 Token 并裁剪（从最老的非 System 消息开始删）
        while sum(len(str(m.get("content", ""))) for m in self.history) > self.max_chars and len(self.history) > 2:
            # 始终保留第一条 System Prompt，弹出第二条
            if self.history[0].get("role") == "system":
                self.history.pop(1)
            else:
                self.history.pop(0)

    def get_context(self) -> list:
        """返回当前的完整上下文"""
        return self.history.copy()
        
    def clear(self):
        self.history.clear()
        logger.info("对话记忆已清空")
