import json
import uuid
from enum import Enum
from typing import List, Dict, Any, Optional

# 引入我们的计算引擎作为"内核 (Kernel)"
from mathlab.core.octave_bridge import OctaveBridge


class CellType(Enum):
    CODE = "code"  # Octave/Python 代码
    MARKDOWN = "markdown"  # 富文本与 LaTeX 公式
    # 计划中的其他类型：MATH, GEO, PLOT, SLIDER 等可以在后续扩展


class NotebookCell:
    """
    笔记本的最小单元
    记录了输入内容、执行状态、输出结果以及独立的 ID
    """

    def __init__(self, cell_type: CellType, content: str = "", language: str = "mathlab"):
        self.id = str(uuid.uuid4())[:8]  # 生成简短的唯一标识符
        self.type = cell_type
        self.content = content
        self.language = language
        self.outputs: List[Dict[str, Any]] = []  # 存储执行结果
        self.execution_count: Optional[int] = None  # 记录执行序号，如 In [1]

    def clear_output(self):
        """清空该单元格的输出"""
        self.outputs = []
        self.execution_count = None

    def execute(self, kernel: OctaveBridge, exec_count: int) -> None:
        """
        执行当前单元格
        :param kernel: 共享的计算上下文环境
        :param exec_count: 当前的执行序号
        """
        self.clear_output()
        self.execution_count = exec_count

        if self.type == CellType.MARKDOWN:
            # Markdown 单元格不需要计算引擎执行，仅标记为成功渲染
            # 后续 UI 层会负责把它转为 HTML
            self.outputs.append({"type": "markdown", "data": self.content})
            return

        if self.type == CellType.CODE:
            try:
                # 丢给我们的 Octave 桥接器去解析和计算
                result = kernel.evaluate(self.content)
                if result is not None:
                    # 成功执行并有返回值
                    self.outputs.append({"type": "result", "data": result, "status": "success"})
            except Exception as e:
                # 捕获语法错误或计算异常
                self.outputs.append({"type": "error", "data": str(e), "status": "failed"})

    def to_dict(self) -> dict:
        """序列化为字典，用于保存文件"""
        # 注意：此处暂不序列化复杂的 outputs（如 numpy 数组），只保存源码
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "language": getattr(self, "language", "mathlab"),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NotebookCell":
        """从字典反序列化"""
        cell = cls(CellType(data["type"]), data["content"], data.get("language", "mathlab"))
        cell.id = data.get("id", cell.id)
        return cell


class MathLabNotebook:
    """
    交互笔记本管理器
    维护所有 Cell 的列表，并持有一个共享的上下文 Kernel。
    """

    def __init__(self):
        self.cells: List[NotebookCell] = []
        self.kernel = OctaveBridge()  # 笔记本拥有独立的计算内核
        self._execution_counter = 0

    def add_cell(
        self,
        cell_type: CellType,
        content: str = "",
        index: int = -1,
        language: str = "mathlab",
    ) -> NotebookCell:
        """在指定位置添加一个新单元格"""
        cell = NotebookCell(cell_type, content, language)
        if index == -1:
            self.cells.append(cell)
        else:
            self.cells.insert(index, cell)
        return cell

    def remove_cell(self, cell_id: str) -> bool:
        """根据 ID 移除单元格"""
        for i, cell in enumerate(self.cells):
            if cell.id == cell_id:
                self.cells.pop(i)
                return True
        return False

    def execute_cell(self, cell_id: str) -> None:
        """独立执行某一个特定的单元格"""
        for cell in self.cells:
            if cell.id == cell_id:
                self._execution_counter += 1
                cell.execute(self.kernel, self._execution_counter)
                break

    def execute_all(self) -> None:
        """从上到下顺序执行所有单元格"""
        # 可以先重置内核状态，保证每次全部运行的结果一致
        self.kernel = OctaveBridge()
        self._execution_counter = 0

        for cell in self.cells:
            self._execution_counter += 1
            cell.execute(self.kernel, self._execution_counter)

    def save_to_file(self, filepath: str) -> None:
        """导出为 .mlnb (MathLab Notebook) JSON 文件"""
        data = {"version": "2.6", "cells": [cell.to_dict() for cell in self.cells]}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load_from_file(self, filepath: str) -> None:
        """从文件加载"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.cells = []
        self._execution_counter = 0
        self.kernel = OctaveBridge()  # 重置内核

        for cell_data in data.get("cells", []):
            self.cells.append(NotebookCell.from_dict(cell_data))
