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
        if self.config.provider == AIProvider.CLAUDE:
            headers['x-api-key'] = self.config.api_key
            headers['anthropic-version'] = '2023-06-01'
        else:
            headers['Authorization'] = f'Bearer {self.config.api_key}'

        model_names = {
            AIProvider.OPENAI: "gpt-4o",
            AIProvider.CLAUDE: "claude-3-5-sonnet-20241022",
            AIProvider.GEMINI: "gemini-1.5-flash",
            AIProvider.DEEPSEEK: "deepseek-chat",
            AIProvider.KIMI: "moonshot-v1-8k",
            AIProvider.MINIMAX: "abab6.5s-chat",
            AIProvider.QWEN: "qwen-plus",
            AIProvider.ZHIPU: "glm-4",
            AIProvider.DOUBAO: "doubao-pro-4k",
            AIProvider.OLLAMA: "qwen2",
        }

        urls = {
            AIProvider.OPENAI: "https://api.openai.com/v1/chat/completions",
            AIProvider.CLAUDE: "https://api.anthropic.com/v1/messages",
            AIProvider.GEMINI: "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            AIProvider.DEEPSEEK: "https://api.deepseek.com/v1/chat/completions",
            AIProvider.KIMI: "https://api.moonshot.cn/v1/chat/completions",
            AIProvider.MINIMAX: "https://api.minimax.chat/v1/text/chatcompletion",
            AIProvider.QWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            AIProvider.ZHIPU: "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            AIProvider.DOUBAO: "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
            AIProvider.OLLAMA: "http://localhost:11434/v1/chat/completions",
        }

        payload = {
            'model': model_names.get(self.config.provider, ""),
            'messages': messages,
            'stream': True,
            'max_tokens': 2048
        }

        url = self.config.base_url or urls.get(self.config.provider)
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
                        # ── 隐患二修复：剥离 LLM 输出中可能包裹的 Markdown 标记 ──
                        decoded = _strip_markdown_json(decoded)
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
                            start_idx = buffer.find('{')
                            while start_idx != -1:
                                brace_count = 0
                                end_idx = -1
                                for i in range(start_idx, len(buffer)):
                                    if buffer[i] == '{':
                                        brace_count += 1
                                    elif buffer[i] == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            end_idx = i
                                            break
                                if end_idx != -1:
                                    possible_json = buffer[start_idx:end_idx+1]
                                    try:
                                        action_data = json.loads(possible_json)
                                        if isinstance(action_data, dict) and 'action' in action_data:
                                            self.action_required.emit(possible_json)
                                            buffer = buffer[:start_idx] + buffer[end_idx+1:]
                                            start_idx = buffer.find('{')
                                            continue
                                    except Exception:
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
        from sklearn.metrics import mean_squared_error
        
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
        mse = float(mean_squared_error(y.numpy(), predictions.reshape(-1, 1)))
        
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
