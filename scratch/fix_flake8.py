import os

def strip_whitespaces(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    with open(filepath, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line.rstrip() + '\n')

files = [
    'mathlab/core/ai_tools.py',
    'mathlab/core/algo_animator.py',
    'mathlab/core/animation.py',
    'mathlab/core/async_workers.py',
    'mathlab/core/canvas_tracker.py',
    'mathlab/core/cas_provider.py'
]

for filepath in files:
    if os.path.exists(filepath):
        strip_whitespaces(filepath)

# Fix ai_manager.py syntax error
with open('mathlab/core/ai_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the broken multiline string
broken_str = 'f"💡 意图: {\n                    s[\'intent\']}\\n```python\\n{\n                    s[\'code\']}\\n```\\n\\n"'
fixed_str = 'f"💡 意图: {s[\'intent\']}\\n```python\\n{s[\'code\']}\\n```\\n\\n"'
content = content.replace(broken_str, fixed_str)

with open('mathlab/core/ai_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done stripping whitespaces and fixing syntax error')
