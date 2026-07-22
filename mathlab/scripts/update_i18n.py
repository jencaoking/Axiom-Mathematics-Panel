import json

files = {
    'j:/PROJECT/Python project/Axiom Mathematics Panel/mathlab/locale/en.json': {
        'workspace_empty': 'Workspace: Empty',
        'clear': 'Clear',
        'reset': 'Reset Workspace',
        'placeholder': 'Enter Octave syntax (e.g. A = [1 2; 3 4] or eig(A)) ...',
        'run': '▶ Run',
        'backend_info': 'Backend: NumPy / SciPy / NumEngine &nbsp;·&nbsp; Syntax: MATLAB/Octave Compatible<br>',
        'hint1': 'Hint: Enter <code style="color:{0};">A = [1 2; 3 4]</code> to build matrix, ',
        'hint2': '<code style="color:{0};">eig(A)</code> for eigenvalues, ↑↓ to browse history',
        'reset_success': '✓ Workspace reset'
    },
    'j:/PROJECT/Python project/Axiom Mathematics Panel/mathlab/locale/zh.json': {
        'workspace_empty': '工作区: 空',
        'clear': '清屏',
        'reset': '重置工作区',
        'placeholder': '输入 Octave 语法（如: A = [1 2; 3 4]  或  eig(A)），Enter 执行 ...',
        'run': '▶ 执行',
        'backend_info': '后端: NumPy / SciPy / NumEngine &nbsp;·&nbsp; 语法: MATLAB/Octave 兼容<br>',
        'hint1': '提示: 输入 <code style="color:{0};">A = [1 2; 3 4]</code> 构建矩阵，',
        'hint2': '<code style="color:{0};">eig(A)</code> 计算特征值，↑↓ 键浏览历史',
        'reset_success': '✓ 工作区已重置'
    }
}

for path, data in files.items():
    with open(path, 'r', encoding='utf8') as f:
        d = json.load(f)
    d.setdefault('math_console', {}).update(data)
    with open(path, 'w', encoding='utf8') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
