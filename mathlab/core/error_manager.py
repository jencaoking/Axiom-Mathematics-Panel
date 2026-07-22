import json
import logging
import os
import sys
import tempfile
import traceback

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStyle,
    QTextEdit,
    QVBoxLayout,
)

logger = logging.getLogger(__name__)

# --- 1. 内置错误知识库 (Knowledge Base) ---
ERROR_KB = {
    "MemoryError": {
        "title": "内存资源紧张",
        "suggestion": "您似乎绘制了过于复杂的解析式或矩阵。建议您关闭部分不需要的图形，或尝试重启软件以释放内存。",
    },
    "PermissionError": {
        "title": "文件权限受限",
        "suggestion": "MathLab 无法写入或保存到该位置。请检查文件是否被其他程序占用，或者尝试以管理员身份运行。",
    },
    "TimeoutError": {
        "title": "计算超时",
        "suggestion": "沙箱中的代码或几何计算耗时过长已被强制中止。请检查是否存在死循环，或尝试简化公式。",
    },
    "JSONDecodeError": {
        "title": "工程文件读取失败",
        "suggestion": "该文件可能已损坏。别担心，您可以尝试从工作区的自动保存备份中恢复 (文件菜单 -> 恢复历史工作区)。",
    },
}


def analyze_error(exc_type, exc_value) -> dict:
    """智能匹配常见问题解答，返回人性化文案"""
    err_name = exc_type.__name__

    # 精准匹配
    if err_name in ERROR_KB:
        return ERROR_KB[err_name]

    # 模糊匹配 (通过扫描异常信息关键字)
    err_msg = str(exc_value).lower()
    if "divide by zero" in err_msg:
        return {
            "title": "数学计算异常",
            "suggestion": "您的公式中触发了除以零的非法操作，请检查分母变量。",
        }

    # 默认兜底文案
    return {
        "title": "哎呀，出了点小状况",
        "suggestion": "MathLab 遇到了一点未知的麻烦。我们已经记录了这个问题，您可以尝试重启软件继续工作。",
    }


class CrashReportDialog(QDialog):
    """
    人性化的错误弹窗与报告收集器
    """

    def __init__(self, exc_type, exc_value, exc_tb, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MathLab - 提示")
        self.setMinimumWidth(450)

        # 提取智能分析结果
        analysis = analyze_error(exc_type, exc_value)
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        self.traceback_data = tb_str

        layout = QVBoxLayout(self)

        # 1. 友好提示区 (带图标)
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
        icon_label.setPixmap(icon.pixmap(48, 48))

        text_layout = QVBoxLayout()
        title_label = QLabel(f"<b>{analysis['title']}</b>")
        title_label.setStyleSheet("font-size: 16px; color: #E74C3C;")
        desc_label = QLabel(analysis["suggestion"])
        desc_label.setWordWrap(True)

        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)
        header_layout.addWidget(icon_label)
        header_layout.addLayout(text_layout)
        layout.addLayout(header_layout)

        # 2. 技术细节区 (默认隐藏)
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setText(tb_str)
        self.details_text.setStyleSheet("font-family: Consolas; font-size: 11px; background: #f4f4f4;")
        self.details_text.setVisible(False)

        # 3. 操作按钮区
        btn_layout = QHBoxLayout()

        self.toggle_btn = QPushButton("查看技术细节")
        self.toggle_btn.setFlat(True)
        self.toggle_btn.clicked.connect(self._toggle_details)

        self.copy_btn = QPushButton("复制错误报告")
        self.copy_btn.clicked.connect(self._copy_to_clipboard)

        self.restart_btn = QPushButton("重启软件")
        self.restart_btn.setStyleSheet("background-color: #3498DB; color: white; padding: 5px 15px;")
        self.restart_btn.clicked.connect(self.accept)  # 连接重启或关闭

        btn_layout.addWidget(self.toggle_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.restart_btn)

        layout.addWidget(self.details_text)
        layout.addLayout(btn_layout)

    def _toggle_details(self):
        is_visible = self.details_text.isVisible()
        self.details_text.setVisible(not is_visible)
        self.toggle_btn.setText("隐藏技术细节" if not is_visible else "查看技术细节")
        self.adjustSize()

    def _copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        report = f"--- MathLab Error Report ---\nOS: {sys.platform}\nPython: {sys.version}\n\n{self.traceback_data}"
        clipboard.setText(report)
        self.copy_btn.setText("已复制！")


def global_exception_handler(exc_type, exc_value, exc_tb):
    """全局未捕获异常处理钩子"""
    # 1. 永远先写入磁盘日志
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))

    # 2. 判断是否存在 Qt 实例且在主线程
    import threading

    app = QApplication.instance()
    if app and threading.current_thread() is threading.main_thread():
        # 显示友好的崩溃弹窗
        dialog = CrashReportDialog(exc_type, exc_value, exc_tb)
        dialog.exec()
    else:
        # 命令行后备输出（非主线程不能创建 QWidget）
        sys.__excepthook__(exc_type, exc_value, exc_tb)


def install_error_handler():
    """在 main.py 启动时调用此函数"""
    sys.excepthook = global_exception_handler


class AutoSaver(QObject):
    def __init__(self, main_window, interval_ms=30000):
        super().__init__(main_window)
        self.main_window = main_window

        # 设定自动保存路径
        self.autosave_file = os.path.join(tempfile.gettempdir(), "mathlab_autosave.json")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._perform_autosave)
        self.timer.start(interval_ms)

    def _perform_autosave(self):
        """静默执行状态快照"""
        try:
            if hasattr(self.main_window, "project_manager") and self.main_window.project_manager:
                workspace_data = self.main_window.project_manager.serialize_current_state()
                with open(self.autosave_file, "w", encoding="utf-8") as f:
                    json.dump(workspace_data, f)
        except Exception as e:
            logger.warning(f"自动保存失败: {e}")

    def check_and_recover(self):
        """在软件启动时调用，检查是否存在异常退出的遗留存档"""
        if os.path.exists(self.autosave_file):
            reply = QMessageBox.question(
                self.main_window,
                "恢复工作区",
                "检测到上次 MathLab 意外关闭。是否要恢复未保存的工作区？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    with open(self.autosave_file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    self.main_window.project_manager.objects = data.get("objects", {}).copy()
                    self.main_window.project_manager.console_history = data.get("console_history", []).copy()
                    self.main_window.project_manager.settings = data.get("settings", {}).copy()

                    # 在画布上重构所有的对象
                    for (
                        obj_id,
                        obj_data,
                    ) in self.main_window.project_manager.objects.items():
                        self.main_window._add_object(obj_data)
                except Exception as e:
                    logger.warning(f"恢复自动保存失败: {e}")

    def clean_up(self):
        """在用户正常点击关闭按钮、正常退出程序时调用"""
        if os.path.exists(self.autosave_file):
            try:
                os.remove(self.autosave_file)
            except Exception as e:
                logger.warning(f"清理自动存档文件失败: {e}")
