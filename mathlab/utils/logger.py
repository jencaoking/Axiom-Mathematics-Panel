# mathlab/utils/logger.py
"""
全局日志系统 (Global Logging System)
=====================================
线程安全，支持滚动切割，自动捕获未处理异常（含 PyQt 崩溃）。

使用方式:
    from mathlab.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Hello")
    logger.error("Something went wrong", exc_info=True)
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# ── 日志目录：mathlab/logs/ ──────────────────────────────────────────────────
LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs"
)

# 主日志文件路径（供外部模块读取，如"打开日志目录"命令）
LOG_FILE = os.path.join(LOG_DIR, "mathlab.log")

# 根 Logger 名称
_LOGGER_NAME = "MathLab"

# 日志格式
_FMT = "[%(asctime)s] [%(levelname)-8s] [%(threadName)s] [%(module)s:%(lineno)d] - %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    file_level: int = logging.DEBUG,
    console_level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,   # 5 MB
    backup_count: int = 3,
) -> logging.Logger:
    """
    初始化全局日志配置，必须在程序启动最早期调用一次。

    参数:
        file_level:    写入文件的最低日志级别（默认 DEBUG）
        console_level: 输出到终端的最低日志级别（默认 INFO）
        max_bytes:     单个日志文件的最大字节数（默认 5 MB）
        backup_count:  保留的备份文件数量（默认 3 个）

    返回:
        已初始化的 MathLab 根 Logger 实例
    """
    # 确保日志目录存在
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)  # 根 logger 捕获所有级别，由 handler 过滤

    # 避免重复初始化（如单元测试中多次 import）
    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(_FMT, datefmt=_DATE_FMT)

    # ── Handler 1: 滚动文件输出（RotatingFileHandler）────────────────────────
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as e:
        # 日志文件无法创建时，退化为只有控制台输出，程序仍可正常运行
        print(f"[MathLab Logger] 警告: 无法创建日志文件 ({e})，将仅使用控制台输出。")

    # ── Handler 2: 控制台输出（StreamHandler）────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ── 接管全局未捕获异常（Crash Reporter）─────────────────────────────────
    def _handle_unhandled_exception(exc_type, exc_value, exc_traceback):
        """
        接管 sys.excepthook：将任何未被 try/except 捕获的致命异常
        写入日志，而不是让程序直接静默崩溃。
        Ctrl+C (KeyboardInterrupt) 保持原有行为，可正常退出。
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical(
            "未捕获的严重异常 (Unhandled Exception) — 程序即将崩溃",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = _handle_unhandled_exception

    # ── 启动标志行 ────────────────────────────────────────────────────────────
    separator = "=" * 60
    logger.info(separator)
    logger.info(
        "MathLab 启动 | 会话时间: %s | Python %s | PID %d",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        sys.version.split()[0],
        os.getpid(),
    )
    logger.info(separator)

    return logger


def get_logger(module_name: str = None) -> logging.Logger:
    """
    便捷获取子 Logger。

    用法::

        from mathlab.utils.logger import get_logger
        logger = get_logger(__name__)

    参数:
        module_name: 通常直接传入 ``__name__``，
                     会生成 ``MathLab.<module_name>`` 的子 logger，
                     自动继承父 logger 的 handler 与级别。

    返回:
        logging.Logger 实例
    """
    if module_name:
        return logging.getLogger(f"{_LOGGER_NAME}.{module_name}")
    return logging.getLogger(_LOGGER_NAME)
