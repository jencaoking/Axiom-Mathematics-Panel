import numpy as np

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.metrics import mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
import os
import json
import time
from enum import Enum

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
    MINIMAX = "minimax"
    KIMI = "kimi"
    DEEPSEEK = "deepseek"
    LOCAL = "local"

class AIRequestConfig:
    def __init__(self, provider: AIProvider = AIProvider.LOCAL, api_key: str = "", base_url: str = ""):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url

class AIRequestWorker:
    def __init__(self, prompt: str, system_context: dict, config: AIRequestConfig = None):
        self.prompt = prompt
        self.system_context = system_context
        self.config = config or AIRequestConfig()
        self._is_running = False
        self._callbacks = {
            'chunk_received': [],
            'action_required': [],
            'finished': [],
            'error': []
        }

    def on(self, event: str, callback):
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def emit(self, event: str, *args):
        for callback in self._callbacks.get(event, []):
            callback(*args)

    def stop(self):
        self._is_running = False

    def run(self):
        self._is_running = True
        try:
            context_str = json.dumps(self.system_context, ensure_ascii=False)
            
            system_prompt = f"""你是一个数学助手，运行在MathLab交互式数学软件中。
当前画布状态: {context_str}

你的能力:
1. 解答数学问题
2. 分析几何图形
3. 通过JSON指令操作画布

如果需要在画布上操作，请输出纯JSON，格式如:
{{"action": "add_point", "x": 1, "y": 2, "name": "A"}}

支持的操作:
- add_point: 添加点 {{"action": "add_point", "x": number, "y": number, "name": string}}
- add_segment: 添加线段 {{"action": "add_segment", "point1_id": string, "point2_id": string}}
- add_circle: 添加圆 {{"action": "add_circle", "center_id": string, "radius": number}}
- add_polygon: 添加多边形 {{"action": "add_polygon", "point_ids": [string]}}
- update_point: 更新点 {{"action": "update_point", "point_id": string, "x": number, "y": number}}
- remove_object: 删除对象 {{"action": "remove_object", "obj_id": string}}
- clear: 清空画布 {{"action": "clear"}}
- solve: 求解 {{"action": "solve", "expression": string}}

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
            self.emit('error', str(e))
        finally:
            self.emit('finished')

    def _simulate_local_response(self, messages):
        responses = [
            ("分析当前画布...\n", None),
            ("我已识别到画布上的几何对象。\n", None),
            ("根据你的问题，我来帮你分析：\n", None),
            ("这是一个数学问题，我可以帮你解答。\n", None),
            ("如果你需要我在画布上绘制图形，请告诉我具体需求。\n", None),
        ]

        for text_chunk, action in responses:
            if not self._is_running:
                break
            
            for word in text_chunk:
                if not self._is_running:
                    break
                self.emit('chunk_received', word)
                time.sleep(0.05)
            
            if action:
                self.emit('action_required', action)

    def _make_api_request(self, messages):
        if not REQUESTS_AVAILABLE:
            self.emit('error', 'requests library not available')
            return

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.config.api_key}'
        }

        model_names = {
            AIProvider.MINIMAX: "abab6.5s-chat",
            AIProvider.KIMI: "moonshot-v1-8k",
            AIProvider.DEEPSEEK: "deepseek-chat"
        }

        urls = {
            AIProvider.MINIMAX: "https://api.minimax.chat/v1/text/chatcompletion",
            AIProvider.KIMI: "https://api.moonshot.cn/v1/chat/completions",
            AIProvider.DEEPSEEK: "https://api.deepseek.com/v1/chat/completions"
        }

        payload = {
            'model': model_names.get(self.config.provider, ""),
            'messages': messages,
            'stream': True,
            'max_tokens': 2048
        }

        url = self.config.base_url or urls.get(self.config.provider)
        if not url:
            self.emit('error', 'Invalid provider or base URL')
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
                        data = json.loads(decoded)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                self.emit('chunk_received', delta['content'])
                    except json.JSONDecodeError:
                        pass
        except requests.exceptions.RequestException as e:
            self.emit('error', str(e))

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

            if epoch % 10 == 0:
                # 通知训练进度（百分比 + 当前 loss）
                progress = int((epoch + 1) / epochs * 100)
                self.emit('training_progress', progress, float(loss.item()))
        
        with torch.no_grad():
            predictions = model(X).numpy().flatten()
        
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
        from .sandbox import SandboxProcess
        
        sandbox = SandboxProcess()
        result = sandbox.run_code(code)
        return result
