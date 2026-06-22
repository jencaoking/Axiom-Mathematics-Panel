import numpy as np
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
    from PyQt5.QtCore import QThread, pyqtSignal as Signal
    QT_AVAILABLE = True
except ImportError:
    try:
        from PySide6.QtCore import QThread, Signal
        QT_AVAILABLE = True
    except ImportError:
        QT_AVAILABLE = False
        QThread = object  # 降级占位，避免语法报错
        Signal = object

try:
    from openai import OpenAI, AuthenticationError, APIConnectionError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI, AuthenticationError, APIConnectionError = object, Exception, Exception

from mathlab.utils.logger import get_logger
logger = get_logger(__name__)

QUIZ_GENERATOR_SCHEMA = {'type': 'function', 'function': {'name': 'generate_math_quiz', 'description': '根据当前的知识点或用户的画布状态，生成一道针对性的数学测试题。', 'parameters': {'type': 'object', 'properties': {'knowledge_point': {'type': 'string', 'description': "本题考查的核心知识点，如 '勾股定理' 或 '导数极值'"}, 'question_text': {'type': 'string', 'description': '题目正文，支持 LaTeX 公式（用 $$ 包裹）'}, 'question_type': {'type': 'string', 'enum': ['multiple_choice', 'fill_in_blank'], 'description': '题目类型：选择题 或 填空题'}, 'options': {'type': 'array', 'items': {'type': 'string'}, 'description': '如果是选择题，提供4个选项数组；如果是填空题，此项传空数组'}, 'correct_answer': {'type': 'string', 'description': "标准答案（如 'A' 或具体的计算数值）"}, 'explanation': {'type': 'string', 'description': '详细的解题思路和步骤'}}, 'required': ['knowledge_point', 'question_text', 'question_type', 'correct_answer', 'explanation']}}}

DRAW_TOOL_SCHEMA = {'type': 'function', 'function': {'name': 'execute_geometry_draw', 'description': '当用户要求画图时，调用此函数在画布上绘制几何图形。', 'parameters': {'type': 'object', 'properties': {'commands': {'type': 'array', 'description': '绘图指令数组', 'items': {'type': 'object', 'properties': {'cmd': {'type': 'string', 'enum': ['add_point', 'add_circle', 'add_polygon', 'add_segment']}, 'x': {'type': 'number'}, 'y': {'type': 'number'}, 'name': {'type': 'string'}, 'radius': {'type': 'number'}, 'points': {'type': 'array', 'items': {'type': 'string'}}, 'center': {'type': 'string'}, 'p1': {'type': 'string'}, 'p2': {'type': 'string'}}, 'required': ['cmd']}}}, 'required': ['commands']}}}

class AIStreamWorker(QThread):
    """
    基于 QThread 的后台流式请求工作线程
    完美隔离网络 I/O，确保 Qt 主界面绝对不卡顿
    """
    chunk_received = Signal(str)           # 收到文本流碎片
    tool_call_received = Signal(str, str)  # 收到完整的工具调用 (name, arguments_json)
    finished = Signal(str)                 # 生成正常结束 (抛出完整的文本内容)
    cancelled = Signal()                   # 被用户优雅中断
    error_occurred = Signal(str)           # 发生异常

    def __init__(self, client: OpenAI, model: str, messages: list, tools: list = None):
        super().__init__()
        self.client = client
        self.model = model
        self.messages = messages
        self.tools = tools
        import threading
        self._cancel_event = threading.Event()

    def cancel(self):
        """触发优雅中断"""
        self._cancel_event.set()
        
    def stop(self):
        self.cancel()

    def run(self):
        try:
            # 构造请求参数
            kwargs = {
                "model": self.model,
                "messages": self.messages,
                "stream": True,
                "temperature": 0.3
            }
            if self.tools:
                kwargs["tools"] = self.tools
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)
            
            full_text = ""
            # 用于拼接流式下发的 tool_calls 碎片
            tool_calls_buffer = {} 

            for chunk in response:
                # 检查中断标志
                if self._cancel_event.is_set():
                    self.cancelled.emit()
                    return

                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                # 1. 处理普通文本流
                if getattr(delta, 'content', None):
                    full_text += delta.content
                    self.chunk_received.emit(delta.content)

                # 2. 处理工具调用流 (Function Calling 碎片拼接)
                if getattr(delta, 'tool_calls', None):
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_buffer:
                            name = (tc.function.name or "") if tc.function else ""
                            tool_calls_buffer[idx] = {"name": name, "arguments": ""}
                        elif tc.function and tc.function.name:
                            tool_calls_buffer[idx]["name"] = tc.function.name
                            
                        if tc.function and tc.function.arguments:
                            tool_calls_buffer[idx]["arguments"] += tc.function.arguments

            # 请求结束后，如果有工具调用，则抛出给主线程执行
            if tool_calls_buffer:
                for tc in tool_calls_buffer.values():
                    # 确保 JSON 参数拼接完整后，抛出信号
                    args = tc["arguments"].strip() or "{}"
                    self.tool_call_received.emit(tc["name"], args)
            
            # 正常结束抛出完整文本
            self.finished.emit(full_text)
            
        except AuthenticationError:
            self.error_occurred.emit("API Key 认证失败，请在设置中检查。")
        except APIConnectionError:
            self.error_occurred.emit("网络连接失败，请检查 Base URL 或代理设置。")
        except Exception as e:
            self.error_occurred.emit(f"AI 引擎异常: {str(e)}")

def _strip_markdown_json(text: str) -> str:
    """剥离 LLM 输出中包裹 JSON 的 Markdown 代码块标记。

    例如将::

        ```json
        {"action": "solve"}
        ```

    转换为::

        {"action": "solve"}

    同时兼容不带语言标识的 ``` 包裹形式。
    """
    # 匹配形如 ```json ... ``` 或 ``` ... ``` 的代码块（允许前后有空白）
    pattern = r'^```(?:json)?\s*\n?(.*?)\n?```$'
    match = re.search(pattern, text.strip(), re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()

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

# 引入配置管理器（线程安全单例：仅在系统启动或显式 reload 时读盘）
from mathlab.core.ai_provider_config import AIProviderConfig

class AIProvider(Enum):
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    KIMI = "kimi"
    MINIMAX = "minimax"
    QWEN = "qwen"
    ZHIPU = "zhipu"
    DOUBAO = "doubao"
    OLLAMA = "ollama"
    LOCAL = "local"

class AIRequestConfig:
    def __init__(self, provider: AIProvider = AIProvider.LOCAL, api_key: str = "", base_url: str = ""):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url

class AIRequestWorker(QThread):
    """AI 请求工作线程。

    继承 QThread，确保阻塞网络请求在后台执行，不阻塞主 UI 线程。
    所有信号均通过 Qt 信号槽机制跨线程安全传递，避免直接在子线程操作 UI。
    """

    # ── Qt 信号定义（跨线程安全） ────────────────────────────────────────────
    chunk_received = Signal(str)
    action_required = Signal(str)
    finished_signal = Signal()
    error_signal = Signal(str)

    def __init__(self, prompt: str, system_context: dict, config: 'AIRequestConfig' = None):
        if QT_AVAILABLE:
            super().__init__()
        else:
            object.__init__(self)
        self.prompt = prompt
        self.system_context = system_context
        self.config = config or AIRequestConfig()
        self._is_running = False

    def stop(self):
        """请求停止（设置标志位，run() 内部会在下次循环检查后退出）。"""
        self._is_running = False

    # ── QThread 入口：由 Qt 在后台线程中自动调用 ─────────────────────────────
    def run(self):
        self._is_running = True
        try:
            context_str = json.dumps(self.system_context, ensure_ascii=False)

            system_prompt = f"""你是一个数学与几何专家，运行在MathLab 2.0 (支持2D/3D交互)中。
当前画布状态: {context_str}

你的能力:
1. 解答复杂的数学、微积分与代数问题
2. 分析 2D 平面与 3D 空间几何图形的拓扑关系
3. 通过JSON指令直接操控用户的画布

如果需要在画布上操作，请输出纯JSON（不要包裹在 Markdown 代码块中），格式如:
{{"action": "add_point", "x": 1, "y": 2, "z": 3, "name": "P"}}

支持的指令:
- add_point: 添加空间点 {{"action": "add_point", "x": number, "y": number, "z": number, "name": string}} (z为可选，默认0)
- add_segment: 添加线段 {{"action": "add_segment", "point1_id": string, "point2_id": string}}
- add_circle: 添加2D圆 {{"action": "add_circle", "center_id": string, "radius": number}}
- add_sphere: 添加3D球体 {{"action": "add_sphere", "center_id": string, "radius": number}}
- update_point: 移动点 {{"action": "update_point", "point_id": string, "x": number, "y": number, "z": number}}
- remove_object: 删除对象 {{"action": "remove_object", "obj_id": string}}
- clear: 清空画布 {{"action": "clear"}}
- solve: 调用SymPy求解 {{"action": "solve", "expression": string}}

注意：如果用户提问涉及 3D（如球体、空间坐标），请务必在指令中包含 z 坐标。
如果只是回答问题，请直接输出文本，不要输出JSON。
"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": self.prompt}
            ]

            if self.config.provider == AIProvider.LOCAL:
                self._simulate_local_response(messages)
            else:
                self._make_api_request(messages)

        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.finished_signal.emit()

    def _simulate_local_response(self, messages):
        # 模拟 AI 生成一段 3D 演示文本和动作
        responses = [
            ("收到！我检测到您的 MathLab 已经升级到 2.0 版本。\n", None),
            ("我将在您的 3D 空间中创建一个坐标为 (2, 3, 4) 的中心点...\n", None),
            ("并在它周围生成一个半径为 5 的空间球体。\n", 
             '{"action": "add_point", "x": 2, "y": 3, "z": 4, "name": "AI_Center"}'),
            # 这里的动作指令由主窗口捕获后执行
            ("请用鼠标在右侧的 3D 画板中拖拽查看效果吧！\n", None),
        ]

        for text_chunk, action in responses:
            if not self._is_running:
                break
            # 模拟打字机效果
            for word in text_chunk:
                if not self._is_running:
                    break
                self.chunk_received.emit(word)
                time.sleep(0.03)

            if action:
                self.action_required.emit(action)

    def _make_api_request(self, messages):
        if not REQUESTS_AVAILABLE:
            self.error_signal.emit('requests library not available')
            return

        headers = {
            'Content-Type': 'application/json',
        }
        # ── 走配置管理器（单例：仅首次实例化时读盘）获取模型/URL/认证方式 ──
        config_manager = AIProviderConfig()
        provider_key = self.config.provider.value if hasattr(self.config.provider, "value") else str(self.config.provider)

        auth_type = config_manager.get_auth_type(provider_key)
        if auth_type == "anthropic":
            headers['x-api-key'] = self.config.api_key
            headers['anthropic-version'] = '2023-06-01'
        else:
            headers['Authorization'] = f'Bearer {self.config.api_key}'

        payload = {
            'model': config_manager.get_model_name(provider_key),
            'messages': messages,
            'stream': True,
            'max_tokens': 2048
        }

        url = self.config.base_url or config_manager.get_api_endpoint(provider_key)
        if not url:
            self.error_signal.emit('Invalid provider or base URL')
            return

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=60
            )
            response.raise_for_status()

            buffer = ""
            for line in response.iter_lines():
                if not self._is_running:
                    break
                if line:
                    try:
                        decoded = line.decode('utf-8')
                        if decoded.startswith('data: '):
                            decoded = decoded[6:]
                        if decoded.strip() == '[DONE]':
                            break
                        # ── 隐患二修复：已移除错误的 _strip_markdown_json 调用 ──
                        data = json.loads(decoded)
                        
                        content = ""
                        # OpenAI / standard format
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                content = delta['content']
                        # Anthropic Claude format
                        elif data.get('type') == 'content_block_delta':
                            delta = data.get('delta', {})
                            if 'text' in delta:
                                content = delta['text']

                        if content:
                            buffer += content
                            decoder = json.JSONDecoder()
                            start_idx = buffer.find('{')
                            while start_idx != -1:
                                try:
                                    action_data, parsed_len = decoder.raw_decode(buffer[start_idx:])
                                    if isinstance(action_data, dict) and 'action' in action_data:
                                        possible_json = buffer[start_idx:start_idx + parsed_len]
                                        self.action_required.emit(possible_json)
                                        buffer = buffer[:start_idx] + buffer[start_idx + parsed_len:]
                                        start_idx = buffer.find('{')
                                        continue
                                except json.JSONDecodeError:
                                    pass
                                start_idx = buffer.find('{', start_idx + 1)
                                
                            safe_idx = buffer.find('{')
                            if safe_idx == -1:
                                if buffer:
                                    self.chunk_received.emit(buffer)
                                    buffer = ""
                            else:
                                safe_text = buffer[:safe_idx]
                                if safe_text:
                                    self.chunk_received.emit(safe_text)
                                buffer = buffer[safe_idx:]
                    except json.JSONDecodeError:
                        pass
            if buffer:
                self.chunk_received.emit(buffer)
        except requests.exceptions.RequestException as e:
            self.error_signal.emit(str(e))

class AIManager:
    def __init__(self):
        self.models = {}
        self.sandbox = None
        self.client = None
        self.current_worker = None
        from mathlab.core.memory_manager import ChatMemoryManager
        self.memory = ChatMemoryManager()
        self.reload_config()

    def reload_config(self):
        """当用户在偏好设置中修改 API 后，自动重载客户端"""
        settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'settings.json')
        settings = {}
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except Exception as e:
                logger.error(f"加载 settings.json 失败: {e}")
                
        api_key = settings.get("ai_api_key", "")
        base_url = settings.get("ai_base_url", "https://api.deepseek.com/v1")
        self.current_model = settings.get("ai_model", "deepseek-chat")
        
        if api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            logger.info(f"AI 引擎已初始化: {base_url} [{self.current_model}]")
        else:
            self.client = None

    def ask(self, user_prompt: str, system_prompt: str = "", history: list = None, 
            on_chunk=None, on_finish=None, on_error=None, **kwargs):
        # 兼容旧 API
        tools = kwargs.get('tools', [DRAW_TOOL_SCHEMA, QUIZ_GENERATOR_SCHEMA])
        on_tool = kwargs.get('on_tool_call')
        # 适配旧 on_finish 签名
        def wrap_finish(text):
            if on_finish: on_finish()
        self.ask_stream(user_prompt, system_prompt, tools, on_chunk, wrap_finish, on_error, on_tool=on_tool)
        return
        
    def ask_old_legacy(self, user_prompt: str, system_prompt: str = "", history: list = None, 
            on_chunk=None, on_finish=None, on_error=None, **kwargs):
        """发起流式对话"""
        if not self.client:
            if on_error:
                on_error("未配置 API Key 或未安装 openai 库，请前往 [设置 -> AI 实验室] 配置。")
            return

        # 如果已有任务在运行，先终止旧任务（防连击）
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.stop()
            self.current_worker.wait()

        tools = kwargs.get('tools', [DRAW_TOOL_SCHEMA, QUIZ_GENERATOR_SCHEMA])
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_prompt})
        
        self.current_worker = AIStreamWorker(self.client, self.current_model, messages, tools=tools)
        
        # 绑定回调信号
        if on_chunk: self.current_worker.chunk_received.connect(on_chunk)
        if on_finish: self.current_worker.finished.connect(on_finish)
        if on_error: self.current_worker.error_occurred.connect(on_error)
        if kwargs.get('on_tool_call'): self.current_worker.tool_call_received.connect(kwargs['on_tool_call'])
        
        self.current_worker.start()
        
    def load_onnx_model(self, model_path, model_name):
        if not ONNX_AVAILABLE:
            return {'success': False, 'error': 'ONNX Runtime not available'}
        
        try:
            import onnxruntime as ort
            session = ort.InferenceSession(model_path)
            self.models[model_name] = {
                'session': session,
                'input_name': session.get_inputs()[0].name,
                'output_name': session.get_outputs()[0].name
            }
            return {'success': True, 'message': f'Model {model_name} loaded successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def predict(self, model_name, input_data):
        if model_name not in self.models:
            return {'success': False, 'error': 'Model not found'}
        
        model = self.models[model_name]
        try:
            input_data = np.array(input_data, dtype=np.float32)
            if len(input_data.shape) == 1:
                input_data = input_data.reshape(1, -1)
            
            result = model['session'].run(
                [model['output_name']],
                {model['input_name']: input_data}
            )
            
            return {'success': True, 'prediction': result[0].tolist()}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def fit_linear_regression(self, points):
        if not SKLEARN_AVAILABLE:
            return {'success': False, 'error': 'scikit-learn not available'}
        if len(points) < 2:
            return {'success': False, 'error': 'Need at least 2 points'}
        
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import mean_squared_error
        
        X = np.array([[p[0]] for p in points], dtype=np.float32)
        y = np.array([p[1] for p in points], dtype=np.float32)
        
        model = LinearRegression()
        model.fit(X, y)
        
        slope = float(model.coef_[0])
        intercept = float(model.intercept_)
        
        predictions = model.predict(X)
        mse = float(mean_squared_error(y, predictions))
        
        return {
            'success': True,
            'slope': slope,
            'intercept': intercept,
            'equation': f'y = {slope:.4f}x + {intercept:.4f}',
            'mse': mse,
            'predictions': predictions.tolist()
        }
    
    def fit_polynomial_regression(self, points, degree=2):
        if not SKLEARN_AVAILABLE:
            return {'success': False, 'error': 'scikit-learn not available'}
        if len(points) < degree + 1:
            return {'success': False, 'error': f'Need at least {degree + 1} points'}
        
        from sklearn.metrics import mean_squared_error
        
        X = np.array([p[0] for p in points], dtype=np.float64)
        y = np.array([p[1] for p in points], dtype=np.float64)
        
        coefficients = np.polyfit(X, y, degree)[::-1]
        poly = np.poly1d(coefficients[::-1])
        
        predictions = poly(X)
        mse = float(mean_squared_error(y, predictions))
        
        # 规范化公式字符串，避免多行输出
        # coefficients 已经是低次到高次排列（经过 [::-1] 反转），i 即为幂次
        terms = []
        for i, c in enumerate(coefficients):
            power = i
            if abs(c) < 1e-10:
                continue
            if power == 0:
                terms.append(f"{c:.4f}")
            elif power == 1:
                terms.append(f"{c:.4f}x")
            else:
                terms.append(f"{c:.4f}x^{power}")
        equation = 'y = ' + ' + '.join(terms) if terms else 'y = 0'
        
        return {
            'success': True,
            'coefficients': coefficients.tolist(),
            'intercept': float(coefficients[0]),  # coefficients[0] 是常数项（低次在前）
            'equation': equation,
            'mse': mse,
            'predictions': predictions.tolist()
        }
    
    def fit_neural_network(self, points, epochs=100, hidden_size=10):
        if not TORCH_AVAILABLE:
            return {'success': False, 'error': 'PyTorch not available'}
        
        if len(points) < 2:
            return {'success': False, 'error': 'Need at least 2 points'}
        
        # [P0修复 Bug1] 补充缺失的导入：mean_squared_error 在此函数中使用但未导入
        import torch
        import torch.nn as nn
        
        X = torch.tensor([[p[0]] for p in points], dtype=torch.float32)
        y = torch.tensor([[p[1]] for p in points], dtype=torch.float32)
        
        model = nn.Sequential(
            nn.Linear(1, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1)
        )
        
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        
        loss_history = []
        
        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = model(X)
            loss = criterion(outputs, y)
            loss.backward()
            optimizer.step()
            
            loss_history.append(float(loss.item()))
        
        with torch.no_grad():
            predictions = model(X).numpy().flatten()
        
        # [P0修复 Bug1] 移除错误的 self.emit()：AIManager 不是 QObject，无此方法
        # 使用 PyTorch 计算 MSE，移除对 sklearn 的隐式依赖
        mse = float(criterion(torch.tensor(predictions).reshape(-1, 1), y).item())
        
        return {
            'success': True,
            'loss_history': loss_history,
            'mse': mse,
            'predictions': predictions.tolist(),
            'epochs': epochs
        }
    
    def cluster_kmeans(self, points, n_clusters=3):
        if not SKLEARN_AVAILABLE:
            return {'success': False, 'error': 'scikit-learn not available'}
        if len(points) < n_clusters:
            return {'success': False, 'error': 'Not enough points for clusters'}
        
        from sklearn.cluster import KMeans
        
        X = np.array(points, dtype=np.float32)
        
        model = KMeans(n_clusters=n_clusters, n_init=10)
        model.fit(X)
        
        labels = model.labels_.tolist()
        centers = model.cluster_centers_.tolist()
        
        return {
            'success': True,
            'labels': labels,
            'centers': centers,
            'inertia': float(model.inertia_)
        }
    
    def cluster_dbscan(self, points, eps=0.5, min_samples=5):
        if not SKLEARN_AVAILABLE:
            return {'success': False, 'error': 'scikit-learn not available'}
        if len(points) < min_samples:
            return {'success': False, 'error': 'Not enough points'}
        
        from sklearn.cluster import DBSCAN
        
        X = np.array(points, dtype=np.float32)
        
        model = DBSCAN(eps=eps, min_samples=min_samples)
        model.fit(X)
        
        labels = model.labels_.tolist()
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        return {
            'success': True,
            'labels': labels,
            'n_clusters': n_clusters,
            'n_noise': list(labels).count(-1)
        }
    
    def recognize_digit(self, image_data):
        if not ONNX_AVAILABLE:
            return {'success': False, 'error': 'ONNX Runtime not available'}
        
        if 'mnist' not in self.models:
            return {'success': False, 'error': 'MNIST model not loaded'}
        
        model = self.models['mnist']
        
        try:
            image_data = np.array(image_data, dtype=np.float32).reshape(1, 1, 28, 28) / 255.0
            
            result = model['session'].run(
                [model['output_name']],
                {model['input_name']: image_data}
            )
            
            predictions = result[0][0]
            top3_indices = np.argsort(predictions)[::-1][:3]
            top3_probs = predictions[top3_indices].tolist()
            top3_digits = top3_indices.tolist()
            
            return {
                'success': True,
                'prediction': int(np.argmax(predictions)),
                'probabilities': predictions.tolist(),
                'top3': [{'digit': d, 'probability': p} for d, p in zip(top3_digits, top3_probs)]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_random_points(self, n=10, x_range=(0, 100), y_range=(0, 100)):
        points = []
        for _ in range(n):
            x = np.random.uniform(x_range[0], x_range[1])
            y = np.random.uniform(y_range[0], y_range[1])
            points.append((x, y))
        return {'success': True, 'points': points}
    
    def run_training_sandbox(self, code):
        try:
            from .sandbox import SandboxProcess
        except ImportError:
            from sandbox import SandboxProcess
        
        sandbox = SandboxProcess()
        result = sandbox.run_code(code)
        return result
    def reload_config(self):
        """从配置中加载 API 密钥 (支持动态热重载)"""
        api_key = self.settings_manager.get("ai_api_key", "") if getattr(self, 'settings_manager', None) else ""
        base_url = self.settings_manager.get("ai_base_url", "https://api.deepseek.com/v1") if getattr(self, 'settings_manager', None) else ""
        self.current_model = self.settings_manager.get("ai_model", "deepseek-chat") if getattr(self, 'settings_manager', None) else "deepseek-chat"
        
        if not api_key:
            api_key = os.environ.get("DEEPSEEK_API_KEY", "")
            
        if api_key:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            logger.info(f"AI 基建就绪 -> {base_url} [{self.current_model}]")
        else:
            self.client = None

    def ask_stream(self, user_prompt: str, system_prompt: str = "", tools: list = None,
                   on_chunk=None, on_finish=None, on_error=None, on_tool=None, on_cancel=None):
        """
        发起带有上下文的流式对话
        """
        if not self.client:
            if on_error: on_error("未配置 API Key。")
            return

        # 压入用户问题到记忆
        self.memory.add_message("user", user_prompt)
        
        # 准备发送给模型的上下文
        messages = self.memory.get_context()
        if system_prompt:
            # System Prompt 永远强行置顶
            messages.insert(0, {"role": "system", "content": system_prompt})

        # 中断上一个未完成的任务
        self.abort_current_task()

        # 启动后台线程
        self.current_worker = AIStreamWorker(self.client, self.current_model, messages, tools)
        
        # 信号绑定
        if on_chunk: self.current_worker.chunk_received.connect(on_chunk)
        if on_error: self.current_worker.error_occurred.connect(on_error)
        if on_tool:  self.current_worker.tool_call_received.connect(on_tool)
        if on_cancel: self.current_worker.cancelled.connect(on_cancel)
        
        # 内部封装 finished，用于自动保存 AI 的回答到记忆中
        def internal_finish(full_text):
            if full_text:
                self.memory.add_message("assistant", full_text)
            if on_finish:
                on_finish(full_text)
                
        self.current_worker.finished.connect(internal_finish)
        self.current_worker.start()

    def abort_current_task(self):
        """优雅中断当前的流式生成"""
        if getattr(self, 'current_worker', None) and self.current_worker.isRunning():
            try:
                self.current_worker.chunk_received.disconnect()
                self.current_worker.finished.disconnect()
                self.current_worker.error_occurred.disconnect()
                self.current_worker.tool_call_received.disconnect()
                self.current_worker.cancelled.disconnect()
            except TypeError:
                pass
            self.current_worker.cancel()
            if not self.current_worker.wait(3000): # 等待线程安全退出
                self.current_worker.terminate()
            self.current_worker = None


