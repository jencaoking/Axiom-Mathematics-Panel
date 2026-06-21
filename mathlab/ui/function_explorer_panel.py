"""
Dynamic Function Explorer Panel - 动态函数探索器

功能:
1. 函数绘图: 支持输入函数解析式并绘制
2. 参数滑块: 对含参数的函数生成滑块,实时更新图象
3. 图象变换: 展示基础函数的平移、伸缩等变换
"""

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QScrollArea, QFrame, QSlider, QGroupBox,
    QMessageBox, QFormLayout, QCheckBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

try:
    from ..utils.i18n_manager import t
except ImportError:
    from utils.i18n_manager import t

import re
import numpy as np


class ParameterSlider(QWidget):
    """单个参数滑块控件"""
    
    value_changed = Signal(str, float)  # param_name, value
    
    def __init__(self, param_name: str, min_val: float = -10.0, 
                 max_val: float = 10.0, default_val: float = 1.0, parent=None):
        super().__init__(parent)
        self.param_name = param_name
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)
        
        # 参数名和当前值显示
        header_layout = QHBoxLayout()
        self.name_label = QLabel(f"{param_name} =")
        self.name_label.setFont(QFont("Consolas", 10))
        self.value_label = QLabel(f"{default_val:.2f}")
        self.value_label.setFont(QFont("Consolas", 10, QFont.Bold))
        self.value_label.setStyleSheet("color: #004ac6;")
        
        header_layout.addWidget(self.name_label)
        header_layout.addStretch()
        header_layout.addWidget(self.value_label)
        layout.addLayout(header_layout)
        
        # 滑块
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(int(min_val * 100), int(max_val * 100))
        self.slider.setValue(int(default_val * 100))
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(int((max_val - min_val) * 10))
        self.slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.slider)
        
    def _on_slider_changed(self, value: int):
        float_value = value / 100.0
        self.value_label.setText(f"{float_value:.2f}")
        self.value_changed.emit(self.param_name, float_value)
    
    def get_value(self) -> float:
        return self.slider.value() / 100.0
    
    def set_value(self, value: float):
        self.slider.setValue(int(value * 100))


class FunctionExplorerPanel(QDockWidget):
    """动态函数探索器面板"""
    
    function_added = Signal(dict)  # 发射函数数据
    function_updated = Signal(dict)  # 更新函数参数
    
    def __init__(self, parent=None):
        super().__init__(t('function_explorer.title'), parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setMinimumWidth(280)
        
        self.current_function_id = None
        self.parameter_sliders = {}  # param_name -> ParameterSlider
        self.function_type = 'explicit'  # explicit, implicit, polar
        
        self._build_ui()
    
    def _build_ui(self):
        """构建UI界面"""
        container = QWidget()
        container.setObjectName("function_explorer_container")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(12)
        
        # === 1. 函数类型选择 ===
        type_group = QGroupBox(t('function_explorer.function_type'))
        type_layout = QVBoxLayout(type_group)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem(t('function_explorer.explicit'), 'explicit')
        self.type_combo.addItem(t('function_explorer.implicit'), 'implicit')
        self.type_combo.addItem(t('function_explorer.polar'), 'polar')
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        
        main_layout.addWidget(type_group)
        
        # === 2. 函数表达式输入 ===
        expr_group = QGroupBox(t('function_explorer.expression'))
        expr_layout = QVBoxLayout(expr_group)
        
        # 示例提示
        self.example_label = QLabel(t('function_explorer.example_explicit'))
        self.example_label.setStyleSheet("color: #737686; font-size: 11px;")
        expr_layout.addWidget(self.example_label)
        
        # 表达式输入框
        self.expr_input = QLineEdit()
        self.expr_input.setPlaceholderText(t('function_explorer.enter_expression'))
        self.expr_input.setFont(QFont("Consolas", 11))
        self.expr_input.returnPressed.connect(self.on_plot_function)
        expr_layout.addWidget(self.expr_input)
        
        # 绘图按钮
        self.plot_btn = QPushButton(t('function_explorer.plot'))
        self.plot_btn.setStyleSheet("""
            QPushButton {
                background: #004ac6;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        self.plot_btn.clicked.connect(self.on_plot_function)
        expr_layout.addWidget(self.plot_btn)
        
        main_layout.addWidget(expr_group)
        
        # === 3. 参数滑块区域 ===
        self.params_group = QGroupBox(t('function_explorer.parameters'))
        params_layout = QVBoxLayout(self.params_group)
        self.params_scroll = QScrollArea()
        self.params_scroll.setWidgetResizable(True)
        self.params_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.params_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.params_container = QWidget()
        self.params_container_layout = QVBoxLayout(self.params_container)
        self.params_container_layout.setContentsMargins(0, 0, 0, 0)
        self.params_container_layout.setSpacing(8)
        self.params_container_layout.addStretch()
        
        self.params_scroll.setWidget(self.params_container)
        params_layout.addWidget(self.params_scroll)
        
        main_layout.addWidget(self.params_group)
        
        # === 4. 图象变换工具 ===
        transform_group = QGroupBox(t('function_explorer.transformations'))
        transform_layout = QVBoxLayout(transform_group)
        
        # 变换按钮行1: 平移
        trans_row1 = QHBoxLayout()
        self.shift_left_btn = QPushButton("← " + t('function_explorer.shift_left'))
        self.shift_right_btn = QPushButton(t('function_explorer.shift_right') + " →")
        self.shift_up_btn = QPushButton("↑ " + t('function_explorer.shift_up'))
        self.shift_down_btn = QPushButton(t('function_explorer.shift_down') + " ↓")
        
        for btn in [self.shift_left_btn, self.shift_right_btn, self.shift_up_btn, self.shift_down_btn]:
            btn.setFixedSize(80, 32)
            btn.setStyleSheet("""
                QPushButton {
                    background: #eff4ff;
                    border: 1px solid #d3e4fe;
                    border-radius: 4px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #d3e4fe;
                }
            """)
        
        trans_row1.addWidget(self.shift_left_btn)
        trans_row1.addWidget(self.shift_right_btn)
        trans_row1.addWidget(self.shift_up_btn)
        trans_row1.addWidget(self.shift_down_btn)
        transform_layout.addLayout(trans_row1)
        
        # 变换按钮行2: 伸缩
        trans_row2 = QHBoxLayout()
        self.scale_x_btn = QPushButton(t('function_explorer.scale_x'))
        self.scale_y_btn = QPushButton(t('function_explorer.scale_y'))
        self.reflect_x_btn = QPushButton(t('function_explorer.reflect_x'))
        self.reflect_y_btn = QPushButton(t('function_explorer.reflect_y'))
        
        for btn in [self.scale_x_btn, self.scale_y_btn, self.reflect_x_btn, self.reflect_y_btn]:
            btn.setFixedSize(80, 32)
            btn.setStyleSheet("""
                QPushButton {
                    background: #eff4ff;
                    border: 1px solid #d3e4fe;
                    border-radius: 4px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #d3e4fe;
                }
            """)
        
        trans_row2.addWidget(self.scale_x_btn)
        trans_row2.addWidget(self.scale_y_btn)
        trans_row2.addWidget(self.reflect_x_btn)
        trans_row2.addWidget(self.reflect_y_btn)
        transform_layout.addLayout(trans_row2)
        
        # 连接变换信号
        self.shift_left_btn.clicked.connect(lambda: self._apply_transform('shift', -1, 0))
        self.shift_right_btn.clicked.connect(lambda: self._apply_transform('shift', 1, 0))
        self.shift_up_btn.clicked.connect(lambda: self._apply_transform('shift', 0, 1))
        self.shift_down_btn.clicked.connect(lambda: self._apply_transform('shift', 0, -1))
        self.scale_x_btn.clicked.connect(lambda: self._apply_transform('scale', 1.5, 1))
        self.scale_y_btn.clicked.connect(lambda: self._apply_transform('scale', 1, 1.5))
        self.reflect_x_btn.clicked.connect(lambda: self._apply_transform('reflect', -1, 1))
        self.reflect_y_btn.clicked.connect(lambda: self._apply_transform('reflect', 1, -1))
        
        main_layout.addWidget(transform_group)
        
        # === 5. 预设函数模板 ===
        template_group = QGroupBox(t('function_explorer.templates'))
        template_layout = QVBoxLayout(template_group)
        
        self.template_combo = QComboBox()
        self.template_combo.addItem(t('function_explorer.template_sine'), 'A*sin(omega*x + phi)')
        self.template_combo.addItem(t('function_explorer.template_quadratic'), 'a*x^2 + b*x + c')
        self.template_combo.addItem(t('function_explorer.template_exponential'), 'a*exp(b*x)')
        self.template_combo.addItem(t('function_explorer.template_gaussian'), 'a*exp(-(x-b)^2/(2*c^2))')
        self.template_combo.addItem(t('function_explorer.template_hyperbola'), 'a/x')
        self.template_combo.currentIndexChanged.connect(self._on_template_selected)
        template_layout.addWidget(self.template_combo)
        
        main_layout.addWidget(template_group)
        
        main_layout.addStretch()
        self.setWidget(container)
    
    def _on_type_changed(self, index: int):
        """函数类型改变时更新示例提示"""
        type_data = self.type_combo.itemData(index)
        examples = {
            'explicit': t('function_explorer.example_explicit'),
            'implicit': t('function_explorer.example_implicit'),
            'polar': t('function_explorer.example_polar')
        }
        self.example_label.setText(examples.get(type_data, ''))
    
    def _on_template_selected(self, index: int):
        """选择预设模板"""
        expression = self.template_combo.itemData(index)
        if expression:
            self.expr_input.setText(expression)
            self.on_plot_function()
    
    def _extract_parameters(self, expression: str) -> list:
        """从表达式中提取参数(非常数变量)"""
        # 已知变量
        known_vars = {'x', 'y', 'theta', 'pi', 'e', 'sin', 'cos', 'tan', 
                      'exp', 'log', 'sqrt', 'abs'}
        
        # 使用正则提取所有字母标识符
        identifiers = re.findall(r'\b([a-zA-Z_]\w*)\b', expression)
        
        # 过滤出参数(非常量、非常见函数)
        params = []
        for ident in identifiers:
            if ident not in known_vars and ident not in params:
                params.append(ident)
        
        return params
    
    def on_plot_function(self):
        """绘制函数"""
        expression = self.expr_input.text().strip()
        if not expression:
            QMessageBox.warning(self, t('dialogs.warning'), 
                              t('function_explorer.empty_expression'))
            return
        
        # 确定函数类型
        func_type = self.type_combo.currentData()
        
        # 提取参数
        params = self._extract_parameters(expression)
        
        # 生成函数对象
        func_data = {
            'type': func_type,
            'expression': expression,
            'parameters': {p: 1.0 for p in params},  # 默认值为1.0
            'x_range': (-10, 10),
            'y_range': (-10, 10),
        }
        
        # 如果是显函数,添加到画布
        if func_type == 'explicit':
            func_data['plot_type'] = 'FunctionPlot'
        elif func_type == 'implicit':
            func_data['plot_type'] = 'ImplicitPlot'
        elif func_type == 'polar':
            func_data['plot_type'] = 'PolarPlot'
        
        # 发射信号
        self.function_added.emit(func_data)
        
        # 创建参数滑块
        self._create_parameter_sliders(params)
    
    def _create_parameter_sliders(self, params: list):
        """为参数创建滑块控件"""
        # 清除旧滑块
        for slider_widget in list(self.parameter_sliders.values()):
            self.params_container_layout.removeWidget(slider_widget)
            slider_widget.deleteLater()
        self.parameter_sliders.clear()
        
        # 创建新滑块
        for param_name in params:
            slider = ParameterSlider(param_name, min_val=-10.0, max_val=10.0, 
                                    default_val=1.0)
            slider.value_changed.connect(self._on_parameter_changed)
            self.parameter_sliders[param_name] = slider
            self.params_container_layout.insertWidget(
                self.params_container_layout.count() - 1, slider
            )
        
        # 显示/隐藏参数组
        self.params_group.setVisible(len(params) > 0)
    
    def _on_parameter_changed(self, param_name: str, value: float):
        """参数值改变时更新函数"""
        if not self.expr_input.text():
            return
        
        # 替换表达式中的参数值
        expression = self.expr_input.text()
        
        # 简单的参数替换(实际应该用更安全的解析)
        try:
            # 将参数名替换为数值
            modified_expr = expression
            for pname, pval in self.parameter_sliders.items():
                val = pval.get_value()
                # 使用正则确保完整匹配参数名
                modified_expr = re.sub(
                    r'\b' + re.escape(pname) + r'\b', 
                    f'({val})', 
                    modified_expr
                )
            
            # 重新绘制
            func_data = {
                'type': self.type_combo.currentData(),
                'expression': modified_expr,
                'original_expression': expression,
                'parameters': {p: s.get_value() for p, s in self.parameter_sliders.items()},
                'x_range': (-10, 10),
                'y_range': (-10, 10),
            }
            
            if self.type_combo.currentData() == 'explicit':
                func_data['plot_type'] = 'FunctionPlot'
            elif self.type_combo.currentData() == 'implicit':
                func_data['plot_type'] = 'ImplicitPlot'
            elif self.type_combo.currentData() == 'polar':
                func_data['plot_type'] = 'PolarPlot'
            
            self.function_updated.emit(func_data)
        except Exception as e:
            print(f"Error updating function: {e}")
    
    def _apply_transform(self, transform_type: str, factor_x: float, factor_y: float):
        """应用图象变换"""
        expression = self.expr_input.text().strip()
        if not expression:
            return
        
        try:
            transformed_expr = expression
            
            if transform_type == 'shift':
                # 平移: f(x-a) + b
                if factor_x != 0:
                    # 水平平移: x -> (x - shift)，使用正则整词匹配避免替换 exp、max 等
                    shift = factor_x
                    transformed_expr = re.sub(r'\bx\b', f'(x - {shift})', transformed_expr)
                if factor_y != 0:
                    # 垂直平移: f(x) + shift
                    shift = factor_y
                    transformed_expr = f'({transformed_expr}) + {shift}'
            
            elif transform_type == 'scale':
                # 伸缩: f(ax) * b
                if factor_x != 1:
                    # 水平伸缩: x -> x/a，使用正则整词匹配
                    transformed_expr = re.sub(r'\bx\b', f'(x / {factor_x})', transformed_expr)
                if factor_y != 1:
                    # 垂直伸缩: f(x) * b
                    transformed_expr = f'{factor_y} * ({transformed_expr})'
            
            elif transform_type == 'reflect':
                # 反射
                if factor_x == -1:
                    # 关于y轴反射: x -> -x，使用正则整词匹配
                    transformed_expr = re.sub(r'\bx\b', '(-x)', transformed_expr)
                if factor_y == -1:
                    # 关于x轴反射: f(x) -> -f(x)
                    transformed_expr = f'-({transformed_expr})'
            
            # 更新表达式并重新绘制
            self.expr_input.setText(transformed_expr)
            self.on_plot_function()
            
        except Exception as e:
            QMessageBox.warning(self, t('dialogs.warning'), 
                              f"{t('function_explorer.transform_error')}: {str(e)}")
    
    def clear_sliders(self):
        """清除所有滑块"""
        for slider_widget in list(self.parameter_sliders.values()):
            self.params_container_layout.removeWidget(slider_widget)
            slider_widget.deleteLater()
        self.parameter_sliders.clear()
        self.params_group.setVisible(False)
    
    def retranslate_ui(self):
        """国际化支持"""
        self.setWindowTitle(t('function_explorer.title'))
        
        # 需要重新翻译的文本
        # 由于使用了组合框和按钮,这里只更新标题
        # 其他文本在创建时已经翻译
