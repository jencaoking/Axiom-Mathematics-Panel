# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — Axiom Mathematics Panel
#
# 运行方式：
#   pyinstaller build_spec.spec

import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, copy_metadata

# 1. 强制收集 JupyterLab 及其底层依赖的所有静态网页资源 (HTML/JS/CSS)
jupyter_datas = collect_data_files('jupyterlab')
jupyter_datas += collect_data_files('notebook')
jupyter_datas += collect_data_files('ipykernel')

# ── 1. 动态收集本地依赖的静态资源 (极其关键) ───────────────────────────────────
app_datas = [
    ('locale', 'locale'),           # 多语言文件
    ('ui/styles.qss', 'ui'),         # 全局样式
    ('ui/icons', 'ui/icons'),       # SVG 图标
    ('docs', 'docs'),               # 文档
    ('resources', 'resources'),     # 资源文件
] + jupyter_datas

# 动态遍历 plugins 目录，把所有 Web 前端工程都打包进去
plugins_dir = 'plugins'
if os.path.exists(plugins_dir):
    for plugin_name in os.listdir(plugins_dir):
        web_path = os.path.join(plugins_dir, plugin_name, 'web')
        if os.path.exists(web_path):
            app_datas.append((web_path, f'plugins/{plugin_name}/web'))

# ── 2. 排除列表（体积优化）──────────────────────────────────────────────────
EXCLUDES = [
    # PyTorch 全家桶
    'torch',
    'torchvision',
    'torchaudio',
    'torch._C',
    'torch.distributions',
    'torch.testing',
    'torch.utils.tensorboard',

    # ONNX
    'onnxruntime',
    'onnx',

    # Matplotlib 无用后端
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
    'PySide6.QtWebEngineQuick',
    'PySide6.QtWebSockets',
    'PySide6.QtXml',

    # 排除 PyQt5 避免打包冲突
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtWebEngineWidgets',
    'PyQt5.QtWebChannel',

    'tkinter',

    # 科学计算中不需要的子包
    'scipy.io.matlab',
    'scipy.ndimage',
    'scipy.signal',
    'scipy.spatial',
    'scipy.stats',

    # sklearn 中不需要的模块
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
    'gi',
    'wx',
]

# ── 3. 分析阶段 ────────────────────────────────────────────────────────────
a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=app_datas,
    hiddenimports=[
        'jupyterlab', 'notebook', 'ipykernel', 'zmq', 
        'IPython', 'requests',
        # WebEngine / PySide6 依赖
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebChannel',
        'PySide6.QtCore',
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
        'numpy',
    ],
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# ── 去掉 PySide6 插件目录中不需要的插件 ────────────────────────────────
def filter_binaries(binaries):
    SKIP_PATTERNS = [
        'qtvirtualkeyboard',
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
        'opengl32sw',   # Mesa 软件渲染
    ]
    result = []
    for name, path, type_ in binaries:
        skip = any(pat.lower() in name.lower() for pat in SKIP_PATTERNS)
        if not skip:
            result.append((name, path, type_))
    return result

a.binaries = filter_binaries(a.binaries)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# ── 图标路径检测 ────────────────────────────────────────────────────────
icon_path = os.path.abspath('resources/icons/app_icon.ico') if os.path.exists('resources/icons/app_icon.ico') else (os.path.abspath('mathlab/resources/icons/app_icon.ico') if os.path.exists('mathlab/resources/icons/app_icon.ico') else None)

# ── 4. 单目录模式 (ONEDIR) ────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MathLab',
    icon=icon_path,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
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

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MathLab',
)

# ── macOS BUNDLE ────────────────────────────────────────────────────────
# 仅在 macOS 上构建 .app Bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='MathLab.app',
        icon=icon_path,
        bundle_identifier='com.mathlab.axiom',
    )
