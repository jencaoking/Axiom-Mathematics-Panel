# mathlab/plugins/calculus_tools/main.py
"""微积分工具插件 — 提供导数/切线、定积分/面积、极限、泰勒展开的可视化计算。"""

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from mathlab.core.extension_api import MathLabAPI
from mathlab.core.plugin_base import MathLabPlugin
from mathlab.utils.i18n_manager import t


class CalculusPanelWidget(QWidget):
    """微积分工具侧边栏面板"""

    def __init__(self, api: MathLabAPI, parent=None):
        super().__init__(parent)
        self.api = api
        self._plotted_ids = []  # 追踪本插件在几何引擎中绘制的对象 ID
        self._init_ui()

    # ──────────────────────────────────────────────────────────────
    # UI 构建
    # ──────────────────────────────────────────────────────────────
    def _init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # ── 标题 ──
        title = QLabel(t("plugins.calculus_tools") or "Calculus Tools")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff; margin-bottom: 6px;")
        layout.addWidget(title)

        # ── 操作模式选择 ──
        mode_group = QGroupBox(t("calculus.mode") or "Mode")
        mode_layout = QVBoxLayout(mode_group)
        self.combo_mode = QComboBox()
        self.combo_mode.addItem(t("calculus.derivative") or "Derivative / Tangent", "derivative")
        self.combo_mode.addItem(t("calculus.definite_integral") or "Definite Integral", "integral")
        self.combo_mode.addItem(t("calculus.limit") or "Limit", "limit")
        self.combo_mode.addItem(t("calculus.taylor_series") or "Taylor Series", "taylor")
        self.combo_mode.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.combo_mode)
        layout.addWidget(mode_group)

        # ── 函数输入 ──
        func_group = QGroupBox(t("calculus.function_input") or "Function Input")
        func_layout = QFormLayout(func_group)
        self.input_expr = QLineEdit()
        self.input_expr.setPlaceholderText("e.g. sin(x), x**2, exp(-x)")
        func_layout.addRow(t("calculus.expression") or "f(x) =", self.input_expr)
        layout.addWidget(func_group)

        # ── 参数区域 (动态切换) ──
        self.param_group = QGroupBox(t("calculus.parameters") or "Parameters")
        self.param_layout = QFormLayout(self.param_group)
        layout.addWidget(self.param_group)

        # 参数控件 — 导数
        self.spin_deriv_x = QDoubleSpinBox()
        self.spin_deriv_x.setRange(-1000, 1000)
        self.spin_deriv_x.setDecimals(4)
        self.spin_deriv_x.setValue(0.0)

        # 参数控件 — 定积分
        self.spin_int_a = QDoubleSpinBox()
        self.spin_int_a.setRange(-1000, 1000)
        self.spin_int_a.setDecimals(4)
        self.spin_int_a.setValue(-1.0)
        self.spin_int_b = QDoubleSpinBox()
        self.spin_int_b.setRange(-1000, 1000)
        self.spin_int_b.setDecimals(4)
        self.spin_int_b.setValue(1.0)

        # 参数控件 — 极限
        self.spin_limit_point = QDoubleSpinBox()
        self.spin_limit_point.setRange(-1000, 1000)
        self.spin_limit_point.setDecimals(4)
        self.spin_limit_point.setValue(0.0)

        # 参数控件 — 泰勒展开
        self.spin_taylor_point = QDoubleSpinBox()
        self.spin_taylor_point.setRange(-1000, 1000)
        self.spin_taylor_point.setDecimals(4)
        self.spin_taylor_point.setValue(0.0)
        self.spin_taylor_order = QSpinBox()
        self.spin_taylor_order.setRange(1, 20)
        self.spin_taylor_order.setValue(5)

        # 初始显示导数参数
        self._on_mode_changed(0)

        # ── 结果显示 ──
        result_group = QGroupBox(t("calculus.result") or "Result")
        result_layout = QVBoxLayout(result_group)
        self.text_result = QTextEdit()
        self.text_result.setReadOnly(True)
        self.text_result.setMaximumHeight(120)
        self.text_result.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #333;")
        result_layout.addWidget(self.text_result)
        layout.addWidget(result_group)

        # ── 操作按钮 ──
        btn_layout = QHBoxLayout()

        self.btn_compute = QPushButton(t("calculus.compute") or "Compute")
        self.btn_compute.setStyleSheet(self._btn_style("#2b579a", "#1e3f7a"))
        self.btn_compute.clicked.connect(self._on_compute)
        btn_layout.addWidget(self.btn_compute)

        self.btn_plot = QPushButton(t("calculus.plot") or "Plot")
        self.btn_plot.setStyleSheet(self._btn_style("#2d7a2d", "#1f5a1f"))
        self.btn_plot.clicked.connect(self._on_plot)
        btn_layout.addWidget(self.btn_plot)

        self.btn_clear = QPushButton(t("calculus.clear") or "Clear")
        self.btn_clear.setStyleSheet(self._btn_style("#7a2d2d", "#5a1f1f"))
        self.btn_clear.clicked.connect(self._on_clear)
        btn_layout.addWidget(self.btn_clear)

        layout.addLayout(btn_layout)
        layout.addStretch()

        scroll.setWidget(inner)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _btn_style(self, bg: str, hover: str) -> str:
        return f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:disabled {{
                background-color: #555;
                color: #aaa;
            }}
        """

    # ──────────────────────────────────────────────────────────────
    # 模式切换 — 动态重建参数区
    # ──────────────────────────────────────────────────────────────
    def _clear_param_layout(self):
        """清空参数布局但不删除控件本身 (removeRow 会删除控件 C++ 对象)"""
        while self.param_layout.count() > 0:
            item = self.param_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def _on_mode_changed(self, index: int):
        self._clear_param_layout()
        mode = self.combo_mode.currentData()

        if mode == "derivative":
            self.param_layout.addRow(t("calculus.eval_point") or "x₀ =", self.spin_deriv_x)
        elif mode == "integral":
            self.param_layout.addRow("a =", self.spin_int_a)
            self.param_layout.addRow("b =", self.spin_int_b)
        elif mode == "limit":
            self.param_layout.addRow(t("calculus.limit_point") or "x →", self.spin_limit_point)
        elif mode == "taylor":
            self.param_layout.addRow(t("calculus.expand_point") or "x₀ =", self.spin_taylor_point)
            self.param_layout.addRow(t("calculus.order") or "Order n =", self.spin_taylor_order)

    # ──────────────────────────────────────────────────────────────
    # 核心引擎访问器 (安全获取)
    # ──────────────────────────────────────────────────────────────
    def _get_engine(self):
        mw = getattr(self.api, "_main_window", None)
        return getattr(mw, "geometry_engine", None) if mw else None

    def _get_cas(self):
        mw = getattr(self.api, "_main_window", None)
        return getattr(mw, "cas_provider", None) if mw else None

    # ──────────────────────────────────────────────────────────────
    # 计算
    # ──────────────────────────────────────────────────────────────
    def _on_compute(self):
        expr_str = self.input_expr.text().strip()
        if not expr_str:
            self._show_error(t("calculus.empty_expr") or "Please enter a function expression.")
            return

        cas = self._get_cas()
        if cas is None:
            self._show_error("CAS provider not available.")
            return

        mode = self.combo_mode.currentData()
        try:
            if mode == "derivative":
                self._compute_derivative(cas, expr_str)
            elif mode == "integral":
                self._compute_integral(cas, expr_str)
            elif mode == "limit":
                self._compute_limit(cas, expr_str)
            elif mode == "taylor":
                self._compute_taylor(cas, expr_str)
        except Exception as e:
            self._show_error(f"{e}")

    def _compute_derivative(self, cas, expr_str: str):
        result = cas.differentiate(expr_str, variable="x")
        if not result.get("success"):
            self._show_error(result.get("error", "Differentiation failed."))
            return

        x0 = self.spin_deriv_x.value()
        # 数值计算 f'(x₀)
        try:
            from sympy import lambdify, symbols

            x_sym = symbols("x")
            deriv_expr = result.get("result", "0")
            func = lambdify(x_sym, deriv_expr, "math")
            slope = float(func(x0))
        except Exception:
            slope = float("nan")

        text = f"f'(x) = {result.get('result', '')}\n" f"f'({x0}) = {slope:.6f}\n" f"LaTeX: {result.get('latex', '')}"
        self.text_result.setPlainText(text)
        self.api.print_to_console(f"[Calculus] f'(x) = {result.get('result', '')}, f'({x0}) ≈ {slope:.6f}")

    def _compute_integral(self, cas, expr_str: str):
        a = self.spin_int_a.value()
        b = self.spin_int_b.value()
        result = cas.definite_integral(expr_str, variable="x", lower=a, upper=b)
        if not result.get("success"):
            self._show_error(result.get("error", "Integration failed."))
            return

        numeric_val = result.get("numeric")
        text = f"∫[{a},{b}] f(x) dx = {result.get('result', '')}\n"
        if numeric_val is not None:
            text += f"Numeric ≈ {numeric_val:.6f}\n"
        text += f"LaTeX: {result.get('latex', '')}"
        self.text_result.setPlainText(text)
        self.api.print_to_console(f"[Calculus] ∫[{a},{b}] = {result.get('result', '')}")

    def _compute_limit(self, cas, expr_str: str):
        point = self.spin_limit_point.value()
        result = cas.limit(expr_str, variable="x", point=point)
        if not result.get("success"):
            self._show_error(result.get("error", "Limit computation failed."))
            return

        text = f"lim(x→{point}) f(x) = {result.get('result', '')}\n" f"LaTeX: {result.get('latex', '')}"
        self.text_result.setPlainText(text)
        self.api.print_to_console(f"[Calculus] lim(x→{point}) = {result.get('result', '')}")

    def _compute_taylor(self, cas, expr_str: str):
        """使用 sympy.series 计算泰勒展开"""
        x0 = self.spin_taylor_point.value()
        n = self.spin_taylor_order.value()
        try:
            from sympy import series, symbols

            x_sym = symbols("x")
            expr = cas.parse_expression(expr_str)
            if expr is None:
                self._show_error("Invalid expression.")
                return
            taylor = series(expr, x_sym, x0, n + 1).removeO()
            from sympy import latex as sympy_latex

            text = f"Taylor(f, x₀={x0}, n={n}):\n" f"  {taylor}\n" f"LaTeX: {sympy_latex(taylor)}"
            self.text_result.setPlainText(text)
            self.api.print_to_console(f"[Calculus] Taylor expansion (n={n}) at x₀={x0}: {taylor}")
        except Exception as e:
            self._show_error(f"Taylor expansion failed: {e}")

    # ──────────────────────────────────────────────────────────────
    # 绘图
    # ──────────────────────────────────────────────────────────────
    def _on_plot(self):
        expr_str = self.input_expr.text().strip()
        if not expr_str:
            self._show_error(t("calculus.empty_expr") or "Please enter a function expression.")
            return

        engine = self._get_engine()
        if engine is None:
            self._show_error("Geometry engine not available.")
            return

        mode = self.combo_mode.currentData()

        # 清除上一次绘制的对象
        self._clear_plotted(engine)

        try:
            if mode == "derivative":
                self._plot_derivative(engine, expr_str)
            elif mode == "integral":
                self._plot_integral(engine, expr_str)
            elif mode == "limit":
                self._plot_limit(engine, expr_str)
            elif mode == "taylor":
                self._plot_taylor(engine, expr_str)
        except Exception as e:
            self._show_error(f"Plot failed: {e}")

    def _plot_derivative(self, engine, expr_str: str):
        """绘制原函数 + 切线"""
        x0 = self.spin_deriv_x.value()

        # 1. 绘制原函数
        func_id = engine.add_function_plot(expr_str, x_range=(x0 - 8, x0 + 8))
        self._plotted_ids.append(func_id)

        # 2. 计算切线方程: y = f(x0) + f'(x0) * (x - x0)
        cas = self._get_cas()
        if cas is None:
            return

        deriv_result = cas.differentiate(expr_str, variable="x")
        if not deriv_result.get("success"):
            return

        from sympy import lambdify, symbols

        x_sym = symbols("x")
        f_expr = cas.parse_expression(expr_str)
        d_expr = cas.parse_expression(deriv_result.get("result", "0"))
        if f_expr is None or d_expr is None:
            return

        f_func = lambdify(x_sym, f_expr, "math")
        d_func = lambdify(x_sym, d_expr, "math")

        try:
            y0 = float(f_func(x0))
            slope = float(d_func(x0))
        except Exception:
            return

        # 切线: y = slope * (x - x0) + y0 => slope*x - slope*x0 + y0
        tangent_expr = f"{slope}*(x-{x0})+{y0}"
        tangent_id = engine.add_function_plot(tangent_expr, x_range=(x0 - 5, x0 + 5))
        self._plotted_ids.append(tangent_id)

        # 3. 标记切点
        point_id = engine.add_point(x0, y0, name="P")
        self._plotted_ids.append(point_id)

        self.api.print_to_console(f"[Calculus] Plotted f(x) and tangent at x={x0}, slope={slope:.4f}", "info")

    def _plot_integral(self, engine, expr_str: str):
        """绘制原函数 + 积分区域标记"""
        a = self.spin_int_a.value()
        b = self.spin_int_b.value()
        if a >= b:
            self._show_error("Lower bound must be less than upper bound.")
            return

        x_min = min(a, b) - 3
        x_max = max(a, b) + 3

        # 1. 绘制原函数
        func_id = engine.add_function_plot(expr_str, x_range=(x_min, x_max))
        self._plotted_ids.append(func_id)

        # 2. 标记积分端点
        from sympy import lambdify, symbols

        x_sym = symbols("x")
        cas = self._get_cas()
        if cas is None:
            return
        f_expr = cas.parse_expression(expr_str)
        if f_expr is None:
            return
        f_func = lambdify(x_sym, f_expr, "math")

        try:
            ya = float(f_func(a))
            yb = float(f_func(b))
            pa_id = engine.add_point(a, ya, name="A")
            pb_id = engine.add_point(b, yb, name="B")
            self._plotted_ids.extend([pa_id, pb_id])
        except Exception:
            pass

        self.api.print_to_console(f"[Calculus] Plotted f(x) with integral bounds [{a}, {b}]", "info")

    def _plot_limit(self, engine, expr_str: str):
        """绘制函数并标记极限点"""
        point = self.spin_limit_point.value()
        x_range = (point - 5, point + 5)

        func_id = engine.add_function_plot(expr_str, x_range=x_range)
        self._plotted_ids.append(func_id)

        # 尝试在极限点处标记
        cas = self._get_cas()
        if cas is None:
            return

        limit_result = cas.limit(expr_str, variable="x", point=point)
        if limit_result.get("success"):
            try:
                limit_val = float(limit_result.get("result", "nan"))
                if np.isfinite(limit_val):
                    pt_id = engine.add_point(point, limit_val, name="L")
                    self._plotted_ids.append(pt_id)
            except (ValueError, TypeError):
                pass

        self.api.print_to_console(f"[Calculus] Plotted f(x) near x→{point}", "info")

    def _plot_taylor(self, engine, expr_str: str):
        """绘制原函数与泰勒逼近多项式"""
        x0 = self.spin_taylor_point.value()
        n = self.spin_taylor_order.value()

        x_range = (x0 - 6, x0 + 6)

        # 1. 绘制原函数
        func_id = engine.add_function_plot(expr_str, x_range=x_range)
        self._plotted_ids.append(func_id)

        # 2. 计算并绘制泰勒多项式
        cas = self._get_cas()
        if cas is None:
            return

        try:
            from sympy import series, symbols

            x_sym = symbols("x")
            expr = cas.parse_expression(expr_str)
            if expr is None:
                return
            taylor = series(expr, x_sym, x0, n + 1).removeO()
            taylor_str = str(taylor)
            if taylor_str and taylor_str != "0":
                taylor_id = engine.add_function_plot(taylor_str, x_range=x_range)
                self._plotted_ids.append(taylor_id)
        except Exception as e:
            self.api.print_to_console(f"[Calculus] Taylor plot warning: {e}", "error")

        self.api.print_to_console(f"[Calculus] Plotted f(x) and Taylor polynomial (n={n}) at x₀={x0}", "info")

    # ──────────────────────────────────────────────────────────────
    # 清理
    # ──────────────────────────────────────────────────────────────
    def _clear_plotted(self, engine):
        """清除本插件之前绘制的所有几何对象"""
        for obj_id in self._plotted_ids:
            try:
                engine.remove_object(obj_id)
            except Exception:
                pass
        self._plotted_ids.clear()

    def _on_clear(self):
        engine = self._get_engine()
        if engine:
            self._clear_plotted(engine)
        self.text_result.clear()
        self.api.print_to_console("[Calculus] Cleared all plotted objects.", "info")

    def _show_error(self, msg: str):
        self.text_result.setPlainText(f"Error: {msg}")
        self.api.print_to_console(f"[Calculus] {msg}", "error")

    def cleanup(self):
        """面板销毁时清理资源"""
        engine = self._get_engine()
        if engine:
            self._clear_plotted(engine)


class CalculusToolsPlugin(MathLabPlugin):
    name = "Calculus Tools"
    version = "1.0.0"
    author = "MathLab Team"
    description = "Derivative/tangent, definite integral, limit, and Taylor series visualization."

    def __init__(self):
        self.api = None
        self.widget = None

    def on_activate(self, api: MathLabAPI):
        self.api = api
        self.widget = CalculusPanelWidget(api)
        api.add_sidebar_panel(t("plugins.calculus_tools") or "Calculus Tools", self.widget)

        # 注册命令
        api.register_command(
            id="calculus.differentiate",
            title=t("calculus.cmd_derivative") or "Calculus: Differentiate",
            action=lambda: self._quick_action("derivative"),
            category="微积分",
        )
        api.register_command(
            id="calculus.integrate",
            title=t("calculus.cmd_integral") or "Calculus: Definite Integral",
            action=lambda: self._quick_action("integral"),
            category="微积分",
        )
        api.register_command(
            id="calculus.limit",
            title=t("calculus.cmd_limit") or "Calculus: Limit",
            action=lambda: self._quick_action("limit"),
            category="微积分",
        )
        api.register_command(
            id="calculus.taylor",
            title=t("calculus.cmd_taylor") or "Calculus: Taylor Series",
            action=lambda: self._quick_action("taylor"),
            category="微积分",
        )

        api.print_to_console("[Calculus Tools] Plugin activated.", color_or_level="info")

    def _quick_action(self, mode: str):
        """命令面板快捷入口：切换到对应模式并聚焦输入框"""
        if self.widget is None:
            return
        idx = self.widget.combo_mode.findData(mode)
        if idx >= 0:
            self.widget.combo_mode.setCurrentIndex(idx)
        self.widget.input_expr.setFocus()
        self.widget._on_compute()

    def on_deactivate(self):
        if self.widget is not None:
            self.widget.cleanup()
            self.widget = None
