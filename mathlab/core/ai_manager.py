import threading
from mathlab.core.skill_manager import SkillLibrary
from mathlab.core.ai_tools import execute_math_task
import numpy as np
import importlib.util

if importlib.util.find_spec('sklearn') is not None:
    SKLEARN_AVAILABLE = True
else:
    SKLEARN_AVAILABLE = False
import os
import json
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
    OpenAI, AuthenticationError, APIConnectionError = object, Exception, Exception  # noqa: E501

from mathlab.utils.logger import get_logger
from mathlab.core.memory_manager import ChatMemoryManager

logger = get_logger(__name__)

QUIZ_GENERATOR_SCHEMA = {
    'type': 'function', 'function': {
        'name': 'generate_math_quiz', 'description': '根据当前的知识点或用户的画布状态，生成一道针对性的数学测试题。', 'parameters': {  # noqa: E501
            'type': 'object', 'properties': {
                'knowledge_point': {
                    'type': 'string', 'description': "本题考查的核心知识点，如 '勾股定理' 或 '导数极值'"}, 'question_text': {  # noqa: E501
                        'type': 'string', 'description': '题目正文，支持 LaTeX 公式（用 $$ 包裹）'}, 'question_type': {  # noqa: E501
                            'type': 'string', 'enum': [
                                'multiple_choice', 'fill_in_blank'], 'description': '题目类型：选择题 或 填空题'}, 'options': {  # noqa: E501
                                    'type': 'array', 'items': {
                                        'type': 'string'}, 'description': '如果是选择题，提供4个选项数组；如果是填空题，此项传空数组'}, 'correct_answer': {  # noqa: E501
                                            'type': 'string', 'description': "标准答案（如 'A' 或具体的计算数值）"}, 'explanation': {  # noqa: E501
                                                'type': 'string', 'description': '详细的解题思路和步骤'}}, 'required': [  # noqa: E501
                                                    'knowledge_point', 'question_text', 'question_type', 'correct_answer', 'explanation']}}}  # noqa: E501

DRAW_TOOL_SCHEMA = {
    'type': 'function', 'function': {
        'name': 'execute_geometry_draw', 'description': '当用户要求画图时，调用此函数在画布上绘制几何图形。', 'parameters': {  # noqa: E501
            'type': 'object', 'properties': {
                'commands': {
                    'type': 'array', 'description': '绘图指令数组', 'items': {
                        'type': 'object', 'properties': {
                            'cmd': {
                                'type': 'string', 'enum': [
                                    'add_point', 'add_circle', 'add_polygon', 'add_segment']}, 'x': {  # noqa: E501
                                        'type': 'number'}, 'y': {
                                            'type': 'number'}, 'name': {
                                                'type': 'string'}, 'radius': {
                                                    'type': 'number'}, 'points': {  # noqa: E501
                                                        'type': 'array', 'items': {  # noqa: E501
                                                            'type': 'string'}}, 'center': {  # noqa: E501
                                                                'type': 'string'}, 'p1': {  # noqa: E501
                                                                    'type': 'string'}, 'p2': {  # noqa: E501
                                                                        'type': 'string'}}, 'required': ['cmd']}}}, 'required': ['commands']}}}  # noqa: E501

# Torch availability check
try:
    import torch  # noqa: F401
    import torch.nn as nn  # noqa: F401
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import onnxruntime as ort  # noqa: F401
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

try:
    import requests  # noqa: F401
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# --- 1. 引入严格的生成状态机 ---


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
    def __init__(self, provider: AIProvider = AIProvider.LOCAL,
                 api_key: str = "", base_url: str = ""):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url


class AIState(Enum):
    IDLE = "空闲"
    THINKING = "思考中..."           # 已发请求，等待首字节 (TTFB)
    GENERATING = "生成中..."         # 正在打字输出
    EXECUTING_TOOL = "执行工具中..."  # 正在调用画笔等本地函数
    FINISHED = "完成"
    ERROR = "出错了"


class AIEngineWorker(QThread):
    """
    统一、纯净的流式 AI 核心线程
    全面废弃野路子正则，严格使用 Function Calling，支持 Token 统计
    """
    state_changed = Signal(AIState)
    chunk_received = Signal(str)
    tool_call_received = Signal(str, object)
    usage_reported = Signal(int, int)
    finished_text = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, client: OpenAI, model: str,
                 messages: list, tools: list = None):
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
            kwargs = {
                "model": self.model,
                "messages": self.messages,
                "stream": True,
                "temperature": 0.3,
                "stream_options": {"include_usage": True}
            }
            if self.tools:
                kwargs["tools"] = self.tools
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)

            full_text = ""
            tool_calls_buffer = {}
            has_started_typing = False

            for chunk in response:
                if self._is_cancelled:
                    break

                if chunk.usage is not None:
                    self.usage_reported.emit(
                        chunk.usage.prompt_tokens,
                        chunk.usage.completion_tokens)
                    continue

                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                if not has_started_typing and (
                        getattr(delta, 'content', None) or getattr(delta, 'tool_calls', None)):  # noqa: E501
                    has_started_typing = True
                    self.state_changed.emit(AIState.GENERATING)

                if getattr(delta, 'content', None):
                    full_text += delta.content
                    self.chunk_received.emit(delta.content)

                if getattr(delta, 'tool_calls', None):
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_buffer:
                            name = (
                                tc.function.name or "") if tc.function else ""
                            tool_calls_buffer[idx] = {
                                "name": name, "arguments": ""}
                        elif tc.function and tc.function.name:
                            tool_calls_buffer[idx]["name"] = tc.function.name

                        if tc.function and tc.function.arguments:
                            tool_calls_buffer[idx]["arguments"] += tc.function.arguments  # noqa: E501

            if tool_calls_buffer:
                self.state_changed.emit(AIState.EXECUTING_TOOL)
                for tc in tool_calls_buffer.values():
                    try:
                        args = json.loads(
                            tc["arguments"]) if tc["arguments"] else {}
                    except (json.JSONDecodeError, TypeError):
                        args = {}
                    self.tool_call_received.emit(tc["name"], args)

            if not self._is_cancelled:
                self.state_changed.emit(AIState.FINISHED)
                self.finished_text.emit(full_text)
            else:
                self.state_changed.emit(AIState.IDLE)

        except Exception as e:
            self.state_changed.emit(AIState.ERROR)
            self.error_occurred.emit(str(e))
            logger.error(f"AI Worker Error: {e}", exc_info=True)


class AIManager(QObject):
    """
    单一职责的全局 AI 调度中心
    """

    def __init__(self, settings_manager=None):
        super().__init__()
        self.settings_manager = settings_manager
        self.client = None
        self.current_worker = None
        self.memory = ChatMemoryManager()
        self.models = {}
        self.sandbox = None
        self.current_model = "deepseek-chat"
        self.reload_config()

    def reload_config(self):
        """当用户在偏好设置中修改 API 后，自动重载客户端"""
        settings_path = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__))),
            'settings.json')
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

    def abort_current_task(self):
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            self.current_worker.wait(5000)

    def ask(self, user_prompt: str, system_prompt: str = "", tools: list = None,  # noqa: E501
            canvas_state: str = None,
            on_state_change=None, on_chunk=None, on_tool=None, on_usage=None, on_finish=None, on_error=None):  # noqa: E501

        if not self.client:
            if on_error:
                on_error("未配置 API Key。")
            return

        self.memory.add_message("user", user_prompt)
        messages = self.memory.get_context()

        dynamic_system_prompt = system_prompt
        if canvas_state and canvas_state != "{}":
            dynamic_system_prompt += f"""\n\n
【系统自动注入的视觉环境上下文】
你可以“看到”用户当前的画板状态。以下是画板上所有几何图形的实时 JSON 快照：
```json
{canvas_state}
```
当用户问“这个图怎么解”、“为什么我画的不对”等模糊问题时，请务必参考上述快照数据进行推导和回答。
"""

        if dynamic_system_prompt:
            messages.insert(
                0, {"role": "system", "content": dynamic_system_prompt})

        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            if not self.current_worker.wait(5000):
                self.current_worker.disconnect()
                # [BUG修复] 移除危险的 terminate()，改为警告并断开连接
                logger.warning("AI Worker 未在 5 秒内停止，已断开信号连接")

        self.current_worker = AIEngineWorker(
            self.client, self.current_model, messages, tools)

        if on_state_change:
            self.current_worker.state_changed.connect(on_state_change)
        if on_chunk:
            self.current_worker.chunk_received.connect(on_chunk)
        if on_tool:
            self.current_worker.tool_call_received.connect(on_tool)
        if on_usage:
            self.current_worker.usage_reported.connect(on_usage)
        if on_error:
            self.current_worker.error_occurred.connect(on_error)

        def internal_finish(full_text):
            if full_text:
                self.memory.add_message("assistant", full_text)
            if on_finish:
                on_finish()

        self.current_worker.finished_text.connect(internal_finish)
        self.current_worker.start()

    def load_onnx_model(self, model_path, model_name):
        if not ONNX_AVAILABLE:
            return {'success': False, 'error': 'ONNX Runtime not available'}

        try:
            session = ort.InferenceSession(model_path)
            self.models[model_name] = {
                'session': session,
                'input_name': session.get_inputs()[0].name,
                'output_name': session.get_outputs()[0].name
            }
            return {'success': True,
                    'message': f'Model {model_name} loaded successfully'}
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
            return {'success': False,
                    'error': f'Need at least {degree + 1} points'}

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
        mse = float(criterion(torch.tensor(
            predictions).reshape(-1, 1), y).item())

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
            return {'success': False, 'error': 'Not enough points for clusters'}  # noqa: E501

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
            image_data = np.array(
                image_data, dtype=np.float32).reshape(
                1, 1, 28, 28) / 255.0

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
                'top3': [{'digit': d, 'probability': p} for d, p in zip(top3_digits, top3_probs)]  # noqa: E501
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


class BaseMathAgent:
    def __init__(self, ai_manager, model="deepseek-chat"):
        self.ai_manager = ai_manager
        self.model = model
        self.max_steps = 5
        self.skill_lib = SkillLibrary()  # 实例化本地技能库
        self.system_prompt = "你是一个资深的数学科研助手与高级 Python 程序员。\n请通过 Thought, Action, Observation 闭环结构的计算过程解决问题。"  # noqa: E501


class GeometryAgent(BaseMathAgent):
    def __init__(self, ai_manager):
        super().__init__(ai_manager)
        self.system_prompt = """你是一个【2D 解析几何与代数专家】。
你的任务是编写 Python 代码，调用 numpy 和 scipy 解决数学问题，并利用现有的全局几何画板环境绘图。
请通过 Thought, Action, Observation 闭环进行。"""


class DataVizAgent(BaseMathAgent):
    def __init__(self, ai_manager):
        super().__init__(ai_manager)
        # 强制将大模型的注意力集中在生成 ECharts 字典上
        self.system_prompt = """你是一个【高级数据可视化专家 (DataVizAgent)】。
你的任务是根据用户的需求，生成极具科技感、配色高级的交互式图表。

【系统环境与限制】
1. 宿主环境已经集成了 Apache ECharts 5.5（支持 gl/3D）。
2. 你绝对不能使用 matplotlib, seaborn 或 plotly！
3. 你必须且只能使用环境内置的渲染桥接器：`mathlab.plugins.echarts_viewer.bridge`。

【代码模板标准】
你的 Action 代码必须严格遵循以下结构：
```python
import numpy as np
from mathlab.plugins.echarts_viewer.bridge import render_chart

# 1. 在这里进行数据计算（如生成随机数、计算3D曲面矩阵等）
# ...

# 2. 严格按照 ECharts Option 标准构建字典
options = {
    "backgroundColor": "transparent", # 保持背景透明以适配主线深色主题
    "tooltip": {"trigger": "item"},
    "series": [
        # 你的数据系列
    ]
}

# 3. 发送给前端渲染
render_chart(options)
```
请通过 Thought 和 Action 闭环来完成任务。要求图表配色具有 Cyberpunk 或暗黑科技感（如深紫、荧光蓝）。"""

    def _llm_generate_code(self, messages):
        # 真正使用时通过 ai_manager.client 调用大模型接口
        try:
            response = self.ai_manager.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1
            )
            suggestion = response.choices[0].message.content if response.choices else ""  # noqa: E501
            suggestion = suggestion.replace(
                "```python\n",
                "").replace(
                "\n```",
                "").replace(
                "```",
                "")
            return suggestion
        except Exception as e:
            print(f"LLM Generate Code Error: {e}")
            return "print('Error generating code')"

    def solve_problem(self, user_prompt: str, on_thought_cb=None,
                      on_code_cb=None, on_finish_cb=None):
        # ============== 1. RAG 检索阶段 ==============
        if on_thought_cb:
            on_thought_cb("🔍 正在检索本地技能库记忆...")

        relevant_skills = self.skill_lib.retrieve_relevant_skills(user_prompt)
        skill_context = ""
        if relevant_skills:
            skill_context = "\n【本地技能库中的成功经验】\n以下是你过去成功写过的类似代码，你可以直接复用或参考它们的 API 调用方式：\n"  # noqa: E501
            for s in relevant_skills:
                skill_context += f"💡 意图: {
                    s['intent']}\n```python\n{
                    s['code']}\n```\n\n"
            if on_thought_cb:
                on_thought_cb(f"⚡ 唤醒了 {len(relevant_skills)} 条历史成功经验！")

        # 将 RAG 内容动态注入到 System Prompt
        system_prompt = f"""{self.system_prompt}
{skill_context}
不要输出多余的 Markdown，必须且只能将代码写在 ```python 块中。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"任务：{user_prompt}"}
        ]

        for step in range(self.max_steps):
            if on_thought_cb:
                on_thought_cb(f"⚙️ 正在生成代码 (第 {step + 1} 次尝试)...")

            code_content = self._llm_generate_code(messages)

            if on_code_cb:
                on_code_cb(code_content)

            # 执行代码
            try:
                execution_result_str = execute_math_task(code_content)
                if isinstance(execution_result_str, dict):
                    execution_result = execution_result_str
                else:
                    execution_result = json.loads(execution_result_str)
            except Exception as e:
                execution_result = {"status": "error", "error": str(e)}

            if execution_result.get("status") == "ok":
                if on_thought_cb:
                    on_thought_cb(
                        f"✅ 沙箱执行成功！输出:\n{
                            execution_result.get(
                                'output', '')}")

                # ============== 2. 触发后台“自我提炼”机制 ==============
                threading.Thread(
                    target=self._reflect_and_save_skill,
                    args=(user_prompt, code_content),
                    daemon=True
                ).start()

                if on_finish_cb:
                    on_finish_cb(True, code_content)
                return {"status": "ok", "code": code_content,
                        "result": execution_result.get("output", "")}
            else:
                error_msg = execution_result.get("error", "未知错误")
                if on_thought_cb:
                    on_thought_cb(
                        f"❌ 代码报错 (第 {step + 1} 次尝试), 正在修正...\n报错内容: {error_msg}")  # noqa: E501

                # 将报错信息加入对话历史，让 AI 修正
                messages.append({"role": "assistant",
                                 "content": f"```python\n{code_content}\n```"})
                messages.append({"role": "user",
                                 "content": f"执行失败，报错如下：\n{error_msg}\n请修正代码。"})  # noqa: E501

        if on_finish_cb:
            on_finish_cb(False, "超出最大重试次数")
        return {"status": "failed", "error": "超出最大重试次数"}

    def _reflect_and_save_skill(self, original_prompt, raw_code):
        """后台静默运行：让大模型把刚刚跑通的特定业务代码，抽象为通用函数库"""
        reflection_prompt = f"""
以下代码成功解决了任务：“{original_prompt}”。
请你将这段代码进行“抽象和提炼”，将其封装成一个或多个通用的 Python 函数，剥离掉与特定题目相关的硬编码数字，并加上中文注释。

你必须严格按照以下 JSON 格式返回，不要包含其他任何文本：
{{
    "intent": "一句话描述这个通用函数解决什么问题（例如：求两条曲线的交点并绘制）",
    "abstract_code": "def your_function():\\n    ..."
}}
"""
        try:
            response = self.ai_manager.client.chat.completions.create(
                model=self.ai_manager.current_model,
                messages=[{"role": "user", "content": reflection_prompt}],
                response_format={"type": "json_object"}  # 强制要求返回 JSON
            )
            result_json = json.loads(response.choices[0].message.content)

            # 存入本地知识库
            self.skill_lib.save_skill(
                result_json["intent"],
                result_json["abstract_code"])
        except Exception as e:
            print(f"技能提炼失败 (后台线程): {e}")
