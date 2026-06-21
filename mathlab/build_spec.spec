# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — Axiom Mathematics Panel
#
# 体积优化策略：
#   1. excludes  —— 排除不需要打包的大型库（torch、matplotlib 后端等）
#   2. collect_submodules —— 只收集真正用到的子模块
#   3. upx=True  —— UPX 压缩（需要额外安装 UPX）
#   4. strip=True —— 剥离调试符号（仅 Linux/macOS 有效）
#
# 运行方式：
#   pyinstaller build_spec.spec
#
# UPX 安装（Windows）：
#   winget install upx  或  scoop install upx

import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# ── 排除列表（体积最大贡献者优先）──────────────────────────────────────
EXCLUDES = [
    # PyTorch 全家桶（~800 MB CPU / ~2 GB CUDA）
    # ai_manager.py 已用 try/except 软依赖，运行时缺失只影响神经网络特性
    'torch',
    'torchvision',
    'torchaudio',
    'torch._C',
    'torch.distributions',
    'torch.testing',
    'torch.utils.tensorboard',

    # ONNX Runtime（~80 MB），同为软依赖
    'onnxruntime',
    'onnx',

    # Matplotlib 后端（只留 Agg，其余后端无需打包）
    'matplotlib.backends.backend_gtk3agg',
    'matplotlib.backends.backend_gtk3cairo',
    'matplotlib.backends.backend_macosx',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_tkagg',
    'matplotlib.backends.backend_webagg',
    'matplotlib.backends.backend_wx',
    'matplotlib.backends.backend_wxagg',

    # PySide6 未使用模块
    'PySide6.Qt3DAnimation',
    'PySide6.Qt3DCore',
    'PySide6.Qt3DExtras',
    'PySide6.Qt3DInput',
    'PySide6.Qt3DLogic',
    'PySide6.Qt3DRender',
    'PySide6.QtBluetooth',
    'PySide6.QtCharts',
    'PySide6.QtDataVisualization',
    'PySide6.QtDesigner',
    'PySide6.QtHelp',
    'PySide6.QtLocation',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'PySide6.QtNfc',
    'PySide6.QtPdf',
    'PySide6.QtPdfWidgets',
    'PySide6.QtPositioning',
    'PySide6.QtPrintSupport',
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtQuick3D',
    'PySide6.QtQuickControls2',
    'PySide6.QtQuickWidgets',
    'PySide6.QtRemoteObjects',
    'PySide6.QtSensors',
    'PySide6.QtSerialBus',
    'PySide6.QtSerialPort',
    'PySide6.QtSql',
    'PySide6.QtStateMachine',
    'PySide6.QtTest',
    'PySide6.QtTextToSpeech',
    'PySide6.QtUiTools',
    'PySide6.QtWebChannel',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineQuick',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebSockets',
    'PySide6.QtXml',

    'tkinter',

    # 科学计算中不需要的子包
    'scipy.io.matlab',
    'scipy.ndimage',
    'scipy.signal',
    'scipy.spatial',
    'scipy.stats',

    # sklearn 中不需要的模块（项目只用 linear_model + preprocessing + cluster + metrics）
    'sklearn.neural_network',
    'sklearn.svm',
    'sklearn.tree',
    'sklearn.ensemble',
    'sklearn.gaussian_process',
    'sklearn.neighbors',
    'sklearn.manifold',
    'sklearn.decomposition',

    # 其他无关库
    'IPython',
    'jupyter',
    'notebook',
    'nbformat',
    'sphinx',
    'docutils',
    'PIL',
    'cv2',
    'pandas',
    'numba',
    'Cython',
    'cffi',
    'gi',  # GTK
    'wx',  # wxPython
    'PyQt5',
    'PyQt6',
]

# ── 数据文件（locale、样式表、资源）──────────────────────────────────────
datas = [
    ('locale',    'locale'),
    ('ui/styles.qss', 'mathlab/ui'),
    ('resources', 'resources'),
]

# ── 分析阶段 ────────────────────────────────────────────────────────────
a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # sympy 动态加载的子模块
        'sympy.parsing.sympy_parser',
        'sympy.core.add',
        'sympy.core.mul',
        'sympy.core.power',
        'sympy.functions.elementary.trigonometric',
        'sympy.functions.elementary.exponential',
        'sympy.functions.elementary.miscellaneous',
        'sympy.integrals',
        'sympy.solvers',
        # jedi 补全
        'jedi',
        'jedi.api',
        'parso',
        # scipy 用到的子模块
        'scipy.optimize._lsq.least_squares',
        'scipy.optimize._minpack',
        # sklearn
        'sklearn.linear_model._base',
        'sklearn.preprocessing._data',
        'sklearn.cluster._kmeans',
        'sklearn.cluster._dbscan_inner',
        'sklearn.metrics._regression',
        # networkx
        'networkx.algorithms',
        'networkx.classes',
    ],
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ── 去掉 PySide6 插件目录中不需要的插件 ────────────────────────────────
def filter_binaries(binaries):
    """移除不需要的 Qt 插件，进一步压缩体积。"""
    SKIP_PATTERNS = [
        'qtvirtualkeyboard',
        'qtwebengine',
        'qtwebview',
        'Qt53D',
        'Qt63D',
        'QtBluetooth',
        'QtLocation',
        'QtMultimedia',
        'QtNfc',
        'QtPositioning',
        'QtQml',
        'QtQuick',
        'QtSensors',
        'QtSerialBus',
        'QtSerialPort',
        'QtStateMachine',
        'QtTextToSpeech',
        'opengl32sw',   # Mesa 软件渲染，体积大，硬件足够时不需要
    ]
    result = []
    for name, path, type_ in binaries:
        skip = any(pat.lower() in name.lower() for pat in SKIP_PATTERNS)
        if not skip:
            result.append((name, path, type_))
    return result


a.binaries = filter_binaries(a.binaries)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── 启动动画 (Splash Screen) ──────────────────────────────────────────────
splash = Splash(
    'mathlab/resources/icons/app_icon.png',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    minify_script=True,
    always_on_top=True
)

# ── 图标路径检测 ────────────────────────────────────────────────────────
icon_path = 'resources/icons/app_icon.ico' if os.path.exists('resources/icons/app_icon.ico') else ('mathlab/resources/icons/app_icon.ico' if os.path.exists('mathlab/resources/icons/app_icon.ico') else None)

# ── 单文件输出 ───────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    splash,
    splash.binaries,
    [],
    name='MathLab',
    icon=icon_path,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,           # Windows 上 strip 无效，保持 False
    upx=True,              # 需要系统安装 UPX：winget install upx
    upx_exclude=[
        # 这些库压缩后启动变慢，不值得压缩
        'vcruntime140.dll',
        'python3*.dll',
        'PySide6*.dll',
        'Qt6*.dll',
    ],
    runtime_tmpdir=None,
    console=False,         # 不显示控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
)

# ── macOS Bundle ────────────────────────────────────────────────────────
app = BUNDLE(
    exe,
    name='MathLab.app',
    icon=icon_path,
    bundle_identifier='com.mathlab.axiom',
)
