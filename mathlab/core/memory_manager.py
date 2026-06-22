class ChatMemoryManager:
    """管理对话上下文，防止 Token 爆炸"""
    def __init__(self, max_history_turns=10, max_chars=8000):
        self.max_history_turns = max_history_turns
        self.max_chars = max_chars  # 粗略估算 Token
        self.history = []

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        self._prune_memory()

    def _prune_memory(self):
        """裁剪策略：保留最新的 N 轮，且总字符数不超标"""
        # 1. 裁剪轮数
        if len(self.history) > self.max_history_turns * 2:
            self.history = self.history[-self.max_history_turns * 2:]
            
        # 2. 裁剪长度
        while sum(len(m["content"]) for m in self.history) > self.max_chars and len(self.history) > 2:
            self.history.pop(0)

    def get_context(self) -> list:
        return self.history.copy()
        
    def clear(self):
        self.history.clear()
