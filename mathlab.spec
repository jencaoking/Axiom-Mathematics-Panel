# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata

block_cipher = None

# 1. 静态资源映射：确保 HTML 渲染器、提示词模板等被正确打包
added_files = [
    ('mathlab/resources/chat_renderer.html', 'mathlab/resources'),
    ('mathlab/config/prompts.yaml', 'mathlab/config'),
    ('mathlab/resources/monaco.html', 'mathlab/resources'),
    ('mathlab/resources/dist/*', 'mathlab/resources/dist'),
    ('MathLab.CSharpEngine/bin/Release/netstandard2.0/*.dll', 'MathLab.CSharpEngine/bin/Release/netstandard2.0'),
    # 若有本地图标，请取消下方注释
    # ('mathlab/resources/icon.ico', 'mathlab/resources')
]
added_files += copy_metadata('jupyter_client')

# 2. 隐式依赖声明：强制打包动态加载的引擎和代理
hidden_imports = [
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineWidgets',
    'mathlab.core.agent_registry',
    'mathlab.core.context_assembler',
    'jupyter_client.provisioning.local_provisioner'
]

a = Analysis(
    ['mathlab/main.py'], 
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PySide2'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 3. 生成 Windows 专属的可执行程序
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MathLab',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # 设为 False 以隐藏黑色控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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

# 4. 生成 macOS 专属的 .app 应用程序包
app = BUNDLE(
    coll,
    name='MathLab.app',
    icon=None,
    bundle_identifier='com.commander.mathlab',
)
