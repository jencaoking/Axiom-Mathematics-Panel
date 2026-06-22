import re
import os

filepath = r"j:\PROJECT\Python project\Axiom Mathematics Panel\mathlab\core\ai_manager.py"
with open(filepath, "r", encoding="utf-8") as f:
    old_content = f.read()

# Extract schemas
schemas = re.search(r"(QUIZ_GENERATOR_SCHEMA\s*=.*?DRAW_TOOL_SCHEMA\s*=.*?\]\}\}\})", old_content, re.DOTALL).group(1)

# Extract ML functions
# from load_onnx_model to the end of run_training_sandbox
ml_funcs = re.search(r"(\s+def load_onnx_model.*?return result)", old_content, re.DOTALL).group(1)

# Extract reload_config (the new one, around line 714)
reload_config_code = re.search(r"(\s+def reload_config\(self\):.*?else:\s+self\.client = None)", old_content, re.DOTALL).group(1)

new_content = f"""import numpy as np
import re
import importlib.util

if importlib.util.find_spec('sklearn') is not None:
    SKLEARN_AVAILABLE = True
else:
    SKLEARN_AVAILABLE = False
import os
import json
import time
from enum import Enum

try:
    from PyQt5.QtCore import QObject, QThread, pyqtSignal as Signal
    QT_AVAILABLE = True
except ImportError:
    try:
        from PySide6.QtCore import QObject, QThread, Signal
        QT_AVAILABLE = True
    except ImportError:
        QT_AVAILABLE = False
        QObject, QThread, Signal = object, object, object

try:
    from openai import OpenAI, AuthenticationError, APIConnectionError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI, AuthenticationError, APIConnectionError = object, Exception, Exception

from mathlab.utils.logger import get_logger
from mathlab.core.memory_manager import ChatMemoryManager

logger = get_logger(__name__)

{schemas}

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# --- 1. 引入严格的生成状态机 ---
class AIState(Enum):
    IDLE = "空闲"
    THINKING = "思考中..."           # 已发请求，等待首字节 (TTFB)
    GENERATING = "生成中..."         # 正在打字输出
    EXECUTING_TOOL = "执行工具中..." # 正在调用画笔等本地函数
    FINISHED = "完成"
    ERROR = "出错了"


class AIEngineWorker(QThread):
    \"\"\"
    统一、纯净的流式 AI 核心线程
    全面废弃野路子正则，严格使用 Function Calling，支持 Token 统计
    \"\"\"
    state_changed = Signal(AIState)
    chunk_received = Signal(str)
    tool_call_received = Signal(str, str)
    usage_reported = Signal(int, int)
    finished_text = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, client: OpenAI, model: str, messages: list, tools: list = None):
        super().__init__()
        self.client = client
        self.model = model
        self.messages = messages
        self.tools = tools
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def stop(self):
        self.cancel()

    def run(self):
        self.state_changed.emit(AIState.THINKING)
        try:
            kwargs = {{
                "model": self.model,
                "messages": self.messages,
                "stream": True,
                "temperature": 0.3,
                "stream_options": {{"include_usage": True}} 
            }}
            if self.tools:
                kwargs["tools"] = self.tools
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)
            
            full_text = ""
            tool_calls_buffer = {{}} 
            has_started_typing = False

            for chunk in response:
                if self._is_cancelled:
                    break

                if chunk.usage is not None:
                    self.usage_reported.emit(chunk.usage.prompt_tokens, chunk.usage.completion_tokens)
                    continue

                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                if not has_started_typing and (getattr(delta, 'content', None) or getattr(delta, 'tool_calls', None)):
                    has_started_typing = True
                    self.state_changed.emit(AIState.GENERATING)

                if getattr(delta, 'content', None):
                    full_text += delta.content
                    self.chunk_received.emit(delta.content)

                if getattr(delta, 'tool_calls', None):
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_buffer:
                            name = (tc.function.name or "") if tc.function else ""
                            tool_calls_buffer[idx] = {{"name": name, "arguments": ""}}
                        elif tc.function and tc.function.name:
                            tool_calls_buffer[idx]["name"] = tc.function.name
                            
                        if tc.function and tc.function.arguments:
                            tool_calls_buffer[idx]["arguments"] += tc.function.arguments

            if tool_calls_buffer:
                self.state_changed.emit(AIState.EXECUTING_TOOL)
                for tc in tool_calls_buffer.values():
                    self.tool_call_received.emit(tc["name"], tc["arguments"])
            
            if not self._is_cancelled:
                self.state_changed.emit(AIState.FINISHED)
                self.finished_text.emit(full_text)
            else:
                self.state_changed.emit(AIState.IDLE)
            
        except Exception as e:
            self.state_changed.emit(AIState.ERROR)
            self.error_occurred.emit(str(e))
            logger.error(f"AI Worker Error: {{e}}", exc_info=True)


class AIManager(QObject):
    \"\"\"
    单一职责的全局 AI 调度中心
    \"\"\"
    def __init__(self, settings_manager=None):
        super().__init__()
        self.settings_manager = settings_manager
        self.client = None
        self.current_worker = None
        self.memory = ChatMemoryManager()
        self.models = {{}}
        self.sandbox = None
        self.current_model = "deepseek-chat"
        self.reload_config()

{reload_config_code}

    def abort_current_task(self):
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            self.current_worker.wait()

    def ask(self, user_prompt: str, system_prompt: str = "", tools: list = None,
            canvas_state: str = None,
            on_state_change=None, on_chunk=None, on_tool=None, on_usage=None, on_finish=None, on_error=None):
        
        if not self.client:
            if on_error: on_error("未配置 API Key。")
            return

        self.memory.add_message("user", user_prompt)
        messages = self.memory.get_context()
        
        dynamic_system_prompt = system_prompt
        if canvas_state and canvas_state != "{{}}":
            dynamic_system_prompt += f\"\"\"\\n\\n
【系统自动注入的视觉环境上下文】
你可以“看到”用户当前的画板状态。以下是画板上所有几何图形的实时 JSON 快照：
```json
{{canvas_state}}
```
当用户问“这个图怎么解”、“为什么我画的不对”等模糊问题时，请务必参考上述快照数据进行推导和回答。
\"\"\"

        if dynamic_system_prompt:
            messages.insert(0, {{"role": "system", "content": dynamic_system_prompt}})

        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            self.current_worker.wait()

        self.current_worker = AIEngineWorker(self.client, self.current_model, messages, tools)
        
        if on_state_change: self.current_worker.state_changed.connect(on_state_change)
        if on_chunk: self.current_worker.chunk_received.connect(on_chunk)
        if on_tool:  self.current_worker.tool_call_received.connect(on_tool)
        if on_usage: self.current_worker.usage_reported.connect(on_usage)
        if on_error: self.current_worker.error_occurred.connect(on_error)
        
        def internal_finish(full_text):
            if full_text: self.memory.add_message("assistant", full_text)
            if on_finish: on_finish(full_text)
            
        self.current_worker.finished_text.connect(internal_finish)
        self.current_worker.start()

{ml_funcs}
"""

with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Replacement successful.")
