from setuptools import setup, find_packages

setup(
    name='mathlab',
    version='1.0.0',
    description='Interactive Mathematics and AI Teaching Software',
    author='MathLab Team',
    packages=find_packages(),
    install_requires=[
        'PySide6>=6.5.0',
        'sympy>=1.12',
        'numpy>=1.26',
        'scipy>=1.11',
        'scikit-learn>=1.3',
        'onnxruntime>=1.16',
        'torch>=2.0',
        'matplotlib>=3.8',
        'pyqtgraph>=0.13',
        'networkx>=3.1',
    ],
    entry_points={
        'console_scripts': [
            'mathlab=mathlab.main:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
