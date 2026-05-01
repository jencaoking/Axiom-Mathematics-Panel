import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import numpy as np
    import sklearn
    import torch
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)

allowed_modules = {'numpy', 'sklearn', 'torch', 'matplotlib', 'math', 'random', 'collections'}

full_code = sys.stdin.read()

for line in full_code.split('\n'):
    if 'import' in line or 'from' in line:
        parts = line.split()
        if parts[0] == 'import':
            module = parts[1].split('.')[0]
            if module not in allowed_modules:
                print(f"Error: Module {module} is not allowed", file=sys.stderr)
                sys.exit(1)
        elif parts[0] == 'from':
            module = parts[1].split('.')[0]
            if module not in allowed_modules:
                print(f"Error: Module {module} is not allowed", file=sys.stderr)
                sys.exit(1)

try:
    exec(full_code)
except Exception as e:
    print(f"Execution error: {e}", file=sys.stderr)
    sys.exit(1)
