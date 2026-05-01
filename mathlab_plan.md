# MathLab 数学与AI教学软件实现计划

## 一、项目概述

本项目是一款交互式数学与AI教学桌面软件，核心功能包括：
- 动态几何画板
- Python编程学习环境
- 算法可视化
- AI辅助学习

## 二、技术栈

| 分类 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| GUI框架 | PySide6 |
| 符号计算 | SymPy |
| 数值计算 | NumPy/SciPy |
| AI/ML | scikit-learn, ONNX Runtime, PyTorch |
| 可视化 | matplotlib, pyqtgraph, networkx |
| 打包 | Nuitka |

## 三、目录结构

```
mathlab/
├── main.py                    # 入口文件
├── setup.py                   # 安装配置
├── requirements.txt           # 依赖列表
├── ui/                        # 前端界面模块
│   ├── __init__.py
│   ├── main_window.py         # 主窗口布局
│   ├── canvas.py              # 几何画布(QGraphicsView)
│   ├── algebra_panel.py       # 代数侧边栏
│   ├── console.py             # Python控制台
│   ├── properties_panel.py    # 属性面板
│   ├── algovis_panel.py       # 算法可视化面板
│   ├── ai_tools_panel.py      # AI工具面板
│   ├── command_bar.py         # 命令输入栏
│   └── styles.qss             # 样式表
├── core/                      # 后端内核模块
│   ├── __init__.py
│   ├── geometry_engine.py     # 几何引擎
│   ├── cas_provider.py        # 符号计算服务
│   ├── algo_animator.py       # 算法动画框架
│   ├── ai_manager.py          # AI管理器
│   ├── python_repl.py         # Python控制台内核
│   ├── sandbox.py             # 沙箱子进程
│   └── signals.py             # 信号定义
├── data/                      # 数据存储
│   ├── __init__.py
│   ├── project.py             # 项目文件管理
│   └── models/                # 预置ONNX模型
├── utils/                     # 工具函数
│   ├── __init__.py
│   ├── latex_renderer.py      # LaTeX渲染
│   └── helpers.py             # 通用辅助函数
└── resources/                 # 资源文件
    ├── icons/                 # SVG图标
    └── resources.qrc          # Qt资源文件
```

## 四、实现步骤

### Phase 1: 基础框架搭建 (第1-2天)
- 创建项目目录结构
- 安装依赖
- 配置Qt资源文件
- 创建基础样式表

### Phase 2: 后端内核实现 (第3-7天)
- `geometry_engine.py`: 几何对象管理、依赖DAG、约束求解
- `cas_provider.py`: SymPy封装、LaTeX输出
- `algo_animator.py`: 算法生成器框架、状态快照
- `python_repl.py`: InteractiveConsole封装
- `sandbox.py`: 子进程执行环境

### Phase 3: 前端界面实现 (第8-15天)
- `main_window.py`: 主窗口布局、工具栏、菜单
- `canvas.py`: QGraphicsView画布、几何对象渲染
- `algebra_panel.py`: 代数关系树形展示
- `console.py`: Python控制台UI
- `properties_panel.py`: 对象属性编辑
- `command_bar.py`: GeoGebra风格命令输入

### Phase 4: AI功能集成 (第16-22天)
- `ai_manager.py`: ONNX模型加载、推理
- `ai_tools_panel.py`: 散点拟合、手写识别、聚类演示
- 沙箱子进程训练功能

### Phase 5: 算法可视化 (第23-28天)
- `algo_animator.py`: 排序、搜索、图论算法
- `algo_vis_panel.py`: 动画播放控制

### Phase 6: 文件管理与辅助功能 (第29-32天)
- 项目保存/打开
- 导出PNG/SVG/LaTeX
- 主题切换
- 国际化支持

### Phase 7: 测试与打包 (第33-35天)
- 单元测试
- Nuitka打包
- Bug修复

## 五、关键类设计

### 5.1 GeometryEngine

```python
class GeometryEngine:
    def __init__(self):
        self.objects = {}          # {id: GeometricObject}
        self.dependencies = DAG()  # 依赖关系图
        self.listeners = []        # 变更监听器
    
    def add_object(self, obj):
        """添加几何对象"""
    
    def remove_object(self, obj_id):
        """移除几何对象"""
    
    def update_object(self, obj_id, **kwargs):
        """更新对象属性，触发依赖更新"""
    
    def solve_constraints(self):
        """求解约束方程"""
    
    def get_dependencies(self, obj_id):
        """获取对象依赖链"""
```

### 5.2 GeometricObject (基类)

```python
class GeometricObject:
    TYPES = ['Point', 'Line', 'Circle', 'Polygon', 'Segment']
    
    def __init__(self, obj_id, name):
        self.id = obj_id
        self.name = name
        self.type = None
        self.coordinates = {}       # 数值坐标
        self.symbolic_expr = None   # 符号表达式
        self.constraints = []       # 约束列表
    
    def update_coordinates(self):
        """根据符号表达式更新数值坐标"""
    
    def to_latex(self):
        """转换为LaTeX表示"""
    
    def serialize(self):
        """序列化用于保存"""
```

### 5.3 PythonREPL

```python
class PythonREPL:
    def __init__(self, namespace=None):
        self.console = code.InteractiveConsole(namespace)
        self.history = []
        self.running = False
    
    def execute(self, code):
        """执行代码，返回输出和错误"""
    
    def complete(self, text):
        """自动补全"""
    
    def stop(self):
        """停止当前执行"""
```

### 5.4 AlgoAnimator

```python
class AlgoAnimator:
    def __init__(self):
        self.current_algorithm = None
        self.generator = None
        self.current_state = None
    
    def load_algorithm(self, algorithm_func, **params):
        """加载算法生成器"""
    
    def step(self):
        """执行一步，返回状态快照"""
    
    def reset(self):
        """重置动画"""
    
    def get_state(self):
        """获取当前状态"""
```

### 5.5 AIManager

```python
class AIManager:
    def __init__(self):
        self.models = {}
        self.sandbox = SandboxProcess()
    
    def load_model(self, model_path, model_name):
        """加载ONNX模型"""
    
    def predict(self, model_name, input_data):
        """执行推理"""
    
    def fit_scatter(self, points, model_type='linear'):
        """拟合散点数据"""
    
    def run_training_sandbox(self, code):
        """在沙箱中运行训练代码"""
```

## 六、主窗口布局

```
┌─────────────────────────────────────────────────────────────────┐
│  File  Edit  View  Tools  Help                                  │
├─────────────────────────────────────────────────────────────────┤
│  [● Point] [─ Segment] [○ Circle] [△ Polygon] [...] [Command]   │
├──────────────┬──────────────────────────────┬──────────────────┤
│              │                              │                  │
│  Algebra     │                              │  Properties      │
│  Panel       │      Geometry Canvas         │  Panel           │
│  ┌─────────┐ │  (QGraphicsView)            │  ┌─────────┐     │
│  │ A=(1,2) │ │                              │  │ Name: A │     │
│  │ B=(3,4) │ │                              │  │ Type:   │     │
│  │ c=Circle│ │                              │  │ Point   │     │
│  └─────────┘ │                              │  └─────────┘     │
│              │                              │                  │
└──────────────┴──────────────────────────────┴──────────────────┘
│  Python Console                                                 │
│  >>> x = 5                                                      │
│  >>> draw_circle((0,0), x)                                      │
│  Circle drawn with radius 5                                     │
└─────────────────────────────────────────────────────────────────┘
```

## 七、信号/槽架构

| 信号 | 发送者 | 接收者 | 用途 |
|------|--------|--------|------|
| objectAdded | GeometryEngine | Canvas, AlgebraPanel | 更新显示 |
| objectUpdated | GeometryEngine | Canvas, AlgebraPanel | 更新显示 |
| objectRemoved | GeometryEngine | Canvas, AlgebraPanel | 更新显示 |
| consoleOutput | PythonREPL | Console | 输出结果 |
| algorithmStep | AlgoAnimator | AlgoVisPanel | 动画步骤 |
| trainingProgress | AIManager | AIToolsPanel | 训练进度 |

## 八、依赖列表

```
PySide6>=6.5.0
sympy>=1.12
numpy>=1.26
scipy>=1.11
scikit-learn>=1.3
onnxruntime>=1.16
torch>=2.0
matplotlib>=3.8
pyqtgraph>=0.13
networkx>=3.1
```

## 九、风险与注意事项

1. **性能优化**: 复杂几何场景需使用QOpenGLWidget加速
2. **线程安全**: 耗时计算必须在QThread中执行
3. **沙箱安全**: 用户代码需限制资源访问和执行时间
4. **打包兼容性**: 使用动态导入处理大型库依赖

---

计划已完成，请确认后开始执行。