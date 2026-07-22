from mathlab.utils.logger import get_logger

logger = get_logger(__name__)


class ChatMemoryManager:
    """
    滑动窗口记忆管理器：防止多轮对话撑爆 Token 限制并节省 API 费用

    [修复] 改进裁剪策略：保留 system 消息和最近的重要上下文
    """

    # 需要优先保留的消息角色
    _PRESERVE_ROLES = {"system", "tool"}

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
        self.history.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": name,
                "content": content,
            }
        )
        self._prune_memory()

    def _prune_memory(self):
        """核心裁剪策略

        [修复] 改进策略：
        1. 始终保留所有 system 消息
        2. 按轮数裁剪非 system 消息
        3. 按字符数裁剪时优先删除最老的非 system、非 tool 消息
        """
        # 1. 按轮数裁剪（保留最新的 N 轮，system 消息不计入轮数）
        system_msgs = [m for m in self.history if m.get("role") == "system"]
        non_system_msgs = [m for m in self.history if m.get("role") != "system"]

        max_messages = self.max_history_turns * 2
        if len(non_system_msgs) > max_messages:
            non_system_msgs = non_system_msgs[-max_messages:]

        self.history = system_msgs + non_system_msgs

        # 2. 按字符数裁剪（优先删除最老的普通消息，保留 system 和 tool 消息）
        while (
            sum(len(str(m.get("content", ""))) for m in self.history) > self.max_chars
            and len(self.history) > 2
        ):
            # 找到第一个可以删除的消息（非 system、非 tool）
            deleted = False
            for i, msg in enumerate(self.history):
                if msg.get("role") not in self._PRESERVE_ROLES:
                    self.history.pop(i)
                    deleted = True
                    break

            if not deleted:
                # 如果只剩 system 和 tool 消息，删除最老的 tool 消息
                for i, msg in enumerate(self.history):
                    if msg.get("role") == "tool":
                        self.history.pop(i)
                        break
                else:
                    # 没有可删除的消息了
                    break

    def get_context(self) -> list:
        """返回当前的完整上下文"""
        return self.history.copy()

    def clear(self):
        self.history.clear()
        logger.info("对话记忆已清空")
