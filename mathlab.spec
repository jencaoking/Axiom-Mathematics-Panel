# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 【核心配置】将所有静态资源按路径映射打包进可执行文件中
added_files = [
    ('mathlab/config/prompts.yaml', 'mathlab/config'),
    ('mathlab/resources/monaco.html', 'mathlab/resources'),
    ('mathlab/resources/markdown.html', 'mathlab/resources'),
    # 如果您有本地的图标文件，也加在这里：
    # ('mathlab/resources/icon.ico', 'mathlab/resources')
]

a = Analysis(
    ['mathlab/main.py'], # 程序入口文件为 mathlab/main.py，如果在根目录没有 main.py 的话。 wait, the user spec had ['main.py']. I will check what's right.
    pathex=[],
    binaries=[],
    datas=added_files, # 注入静态资源
    hiddenimports=[
        # 防止部分动态加载的包被 PyInstaller 漏掉
        'mathlab.core.ai_tools_schema',
        'mathlab.core.prompt_manager'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 生成可执行文件配置
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
    console=False, # 设为 False 隐藏黑色的命令行控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='mathlab/resources/icon.ico' # 可选：指定您的软件图标
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

# 针对 macOS 的专属应用包生成
app = BUNDLE(
    coll,
    name='MathLab.app',
    icon=None,
    bundle_identifier='com.yourname.mathlab',
)
