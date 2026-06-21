"""command_manager.py — 全局命令注册中心

纯逻辑层，不依赖任何 GUI 框架。
CommandPalette (UI) 通过 CommandManager 搜索/触发命令；
MainWindow 负责向 CommandManager 注册具体行为。
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional
from mathlab.utils.logger import get_logger

logger = get_logger(__name__)


class Command:
    """描述一条可被用户触发的操作。"""

    def __init__(
        self,
        id: str,
        title: str,
        action: Callable[[], None],
        category: str = "通用",
        shortcut: str = "",
        description: str = "",
    ):
        self.id = id                  # 唯一标识，如 "panel.algebra"
        self.title = title            # 显示名，如 "切换到代数面板"
        self.action = action          # 无参回调
        self.category = category      # 分类标签，如 "视图"、"系统"
        self.shortcut = shortcut      # 仅用于显示，如 "Ctrl+1"
        self.description = description  # 附加说明，显示在副标题

    # ── 模糊匹配打分 ──────────────────────────────────────────────
    def match_score(self, query: str) -> int:
        """返回匹配分数（0 表示不匹配）。越高越相关。"""
        if not query:
            return 1  # 空查询时全部显示

        q = query.lower()
        title_lower = self.title.lower()
        id_lower = self.id.lower()
        cat_lower = self.category.lower()
        desc_lower = self.description.lower()

        # 精确前缀 > 包含匹配 > category 匹配 > id 匹配
        if title_lower.startswith(q):
            return 100
        if q in title_lower:
            return 80
        if cat_lower.startswith(q) or q in cat_lower:
            return 60
        if q in id_lower:
            return 40
        if q in desc_lower:
            return 20

        # 字符序列模糊匹配（所有字符按顺序出现即可）
        idx = 0
        for ch in q:
            pos = title_lower.find(ch, idx)
            if pos == -1:
                return 0
            idx = pos + 1
        return 10

    def __repr__(self) -> str:
        return f"<Command id={self.id!r} title={self.title!r}>"


class CommandManager:
    """命令注册表，负责注册、注销、搜索命令。"""

    def __init__(self):
        self._commands: Dict[str, Command] = {}

    # ── 注册 / 注销 ───────────────────────────────────────────────
    def register(self, command: Command) -> None:
        """注册一条命令（同 id 覆盖旧命令）。"""
        self._commands[command.id] = command

    def unregister(self, command_id: str) -> bool:
        """注销指定 id 的命令，返回是否成功。"""
        if command_id in self._commands:
            del self._commands[command_id]
            return True
        return False

    def get(self, command_id: str) -> Optional[Command]:
        return self._commands.get(command_id)

    # ── 搜索 ─────────────────────────────────────────────────────
    def search(self, query: str, limit: int = 50) -> List[Command]:
        """模糊搜索命令，按相关性降序返回。"""
        scored = [
            (cmd.match_score(query), cmd)
            for cmd in self._commands.values()
        ]
        # 过滤掉不匹配的，按分数降序，再按 category+title 字母序稳定排序
        results = [
            cmd for score, cmd in
            sorted(scored, key=lambda x: (-x[0], x[1].category, x[1].title))
            if score > 0
        ]
        return results[:limit]

    def execute(self, command_id: str) -> bool:
        """按 id 直接执行命令，返回是否找到并执行。"""
        cmd = self._commands.get(command_id)
        if cmd:
            try:
                cmd.action()
            except Exception as e:
                logger.error("执行命令 '%s' 时异常: %s", command_id, e, exc_info=True)
            return True
        return False

    @property
    def all_commands(self) -> List[Command]:
        return list(self._commands.values())

    def categories(self) -> List[str]:
        """返回所有已注册的分类（去重、排序）。"""
        return sorted(set(cmd.category for cmd in self._commands.values()))
