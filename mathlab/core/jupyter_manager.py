"""
jupyter_manager.py
──────────────────
后台 JupyterLab 服务管理器

负责：
  1. 动态占用一个空闲端口（防止与系统 8888 冲突）
  2. 用 subprocess 静默启动 JupyterLab
  3. 等待服务真正就绪（HTTP 200 探测）
  4. 在 Qt closeEvent 中被调用时优雅销毁后台进程
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import threading
from typing import Optional

# ── 软依赖：requests（如不存在则退化为 TCP 探活） ──────────────────────────
try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


class JupyterManager:
    """后台 JupyterLab 服务管理器（线程安全）"""

    def __init__(self) -> None:
        self.port: int = self._get_free_port()
        self.process: Optional[subprocess.Popen] = None
        # 禁用 Token/密码（纯本地沙盒），允许跨域嵌入
        # 🌟 魔法参数：强制暗色主题 + 简单模式
        self.url: str = f"http://localhost:{self.port}/lab?theme=JupyterLab%20Dark&simple=1"
        self._is_ready: bool = False
        self._lock = threading.Lock()

    # ── 端口工具 ────────────────────────────────────────────────────────────

    @staticmethod
    def _get_free_port() -> int:
        """动态获取一个空闲的系统端口，防止 8888 冲突"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]

    # ── 启动 ────────────────────────────────────────────────────────────────

    def start(self, timeout: int = 30) -> bool:
        """
        静默启动 JupyterLab 并阻塞等待就绪。

        Parameters
        ----------
        timeout : int
            最长等待秒数（JupyterLab 首次启动可能需要 15-20 s）

        Returns
        -------
        bool
            True = 服务已就绪；False = 超时或启动失败
        """
        with self._lock:
            if self.process is not None:
                return self._is_ready  # 防重入

        # 🌟 适配 PyInstaller 环境的启动方式 🌟
        # sys.executable 在打包后指向 MathLab.exe，在开发时指向 python.exe
        # 我们使用 -m jupyterlab 来确保它从当前解释器环境中寻找模块
        cmd = [
            sys.executable, "-m", "jupyterlab", 
            "--no-browser", 
            f"--port={self.port}", 
            "--ServerApp.token=''", 
            "--ServerApp.password=''",
            "--ServerApp.allow_origin='*'",
            "--ServerApp.disable_check_xsrf=True"
        ]

        kwargs: dict = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
        }

        # Windows：防止出现黑色 cmd 窗口
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        try:
            proc = subprocess.Popen(cmd, **kwargs)
        except FileNotFoundError:
            print(
                "⚠️  未找到 jupyter 可执行文件。\n"
                "   请运行：pip install jupyterlab\n"
                f"   （当前尝试路径：{jupyter_exe}）"
            )
            return False

        with self._lock:
            self.process = proc

        print(f"🚀 JupyterLab 正在后台启动（端口 {self.port}）…")
        self._wait_until_ready(timeout)
        return self._is_ready

    @staticmethod
    def _resolve_jupyter() -> str:
        """
        尝试解析当前 Python 环境对应的 jupyter 可执行文件路径。
        这样即便不在激活的 venv 里，也能找到正确的 jupyter。
        """
        # sys.executable → .../venv/Scripts/python.exe （Windows）
        scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
        candidate_win = os.path.join(scripts_dir, "jupyter.exe")
        if os.path.isfile(candidate_win):
            return candidate_win

        # Unix-like：bin 目录
        bin_dir = os.path.join(os.path.dirname(sys.executable))
        candidate_unix = os.path.join(bin_dir, "jupyter")
        if os.path.isfile(candidate_unix):
            return candidate_unix

        # 兜底：让 PATH 去找
        return "jupyter"

    # ── 就绪探测 ────────────────────────────────────────────────────────────

    def _wait_until_ready(self, timeout: int) -> None:
        """轮询探测 JupyterLab HTTP 端口，直到就绪或超时"""
        deadline = time.monotonic() + timeout
        url = self.url

        while time.monotonic() < deadline:
            if self.process and self.process.poll() is not None:
                print("❌ JupyterLab 进程意外退出，请检查 stderr。")
                return

            if _HAS_REQUESTS:
                try:
                    resp = _requests.get(url, timeout=2)
                    if resp.status_code < 400:
                        self._is_ready = True
                        print(f"✅ JupyterLab 已在 {url} 后台就绪！")
                        return
                except _requests.ConnectionError:
                    pass
                except Exception:
                    pass
            else:
                # 降级：仅做 TCP 连通测试
                try:
                    with socket.create_connection(("localhost", self.port), timeout=1):
                        self._is_ready = True
                        print(f"✅ JupyterLab 端口 {self.port} 已开放（TCP 探测）。")
                        return
                except OSError:
                    pass

            time.sleep(0.8)

        print(
            f"⚠️  JupyterLab 启动超时（>{timeout}s），界面可能仍在加载。\n"
            "   QWebEngineView 会持续重试，请稍候。"
        )

    # ── 停止 ────────────────────────────────────────────────────────────────

    def stop(self) -> None:
        """
        优雅销毁后台 JupyterLab 进程。
        先发 SIGTERM，等待 3 秒，若仍存活则强制 SIGKILL。
        """
        with self._lock:
            proc = self.process
            self.process = None
            self._is_ready = False

        if proc is None:
            return

        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

        print("🛑 JupyterLab 后台服务已优雅关闭。")

    # ── 状态查询 ────────────────────────────────────────────────────────────

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def is_running(self) -> bool:
        with self._lock:
            return self.process is not None and self.process.poll() is None
