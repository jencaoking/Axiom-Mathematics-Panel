import markdown
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QComboBox, QSpinBox,
    QLabel, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsLineItem,
    QProgressBar, QPlainTextEdit, QTextBrowser, QLineEdit
)

try:
    from .code_editor import AutocompleteTextEdit
except ImportError as e:
    if "attempted relative import" not in str(e) and "No module named" not in str(e):
        raise
    from code_editor import AutocompleteTextEdit
from PySide6.QtGui import QPen, QBrush, QColor, QTextCursor
from PySide6.QtCore import Qt, Signal, QThread, QObject

try:
    from ..utils.i18n_manager import t
except ImportError as e:
    if "attempted relative import" not in str(e) and "No module named" not in str(e):
        raise
    from utils.i18n_manager import t

try:
    from ..core.ai_manager import AIRequestWorker, AIRequestConfig, AIProvider
except ImportError as e:
    if "attempted relative import" not in str(e) and "No module named" not in str(e):
        raise
    from core.ai_manager import AIRequestWorker, AIRequestConfig, AIProvider

try:
    from ..ui.animations import start_breathing_effect
except ImportError as e:
    if "attempted relative import" not in str(e) and "No module named" not in str(e):
        raise
    from ui.animations import start_breathing_effect


NL2DRAW_SYSTEM_PROMPT = """
你是一个名为 MathLab 的高级数学计算与几何绘图助理。
除了回答常规数学问题，你还可以通过输出特定的 JSON 指令，直接在用户的画布上绘图！

如果用户的请求包含明确的【画图、绘制、添加】等意图，你必须在回答的末尾，附带一个纯净的 Markdown JSON 代码块，里面是一个指令数组。
支持的指令 cmd 包括： 'add_point', 'add_circle', 'add_polygon', 'add_segment'

注意：
1. 坐标和距离如果没有指定，请运用几何常识合理分配数值，保证图形美观在视野中央。
2. 务必使用 ```json ... ``` 标签包裹指令数组。

示例场景：用户说"帮我画一个直角三角形"
你的回答应该是：
好，我已经为您在画布上绘制了一个直角三角形。
```json
[
  {"cmd": "add_point", "name": "A", "x": 0, "y": 0},
  {"cmd": "add_point", "name": "B", "x": 4, "y": 0},
  {"cmd": "add_point", "name": "C", "x": 0, "y": 3},
  {"cmd": "add_polygon", "points": ["A", "B", "C"]}
]
```
"""

class AIToolsPanel(QDockWidget):
    fit_requested = Signal(list, str, dict)
    cluster_requested = Signal(list, str, dict)
    recognize_requested = Signal(list)
    generate_points = Signal(int)
    action_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(t('ai_tools.title'), parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.worker = None  # AIRequestWorker(QThread) 实例

        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)

        self.tab_widget = QTabWidget()

        # ------------------------------------------------------------------
        # Tab 0: Scatter Fitting
        # ------------------------------------------------------------------
        self.scatter_tab = QWidget()
        self.scatter_layout = QVBoxLayout(self.scatter_tab)

        self.model_combo = QComboBox()
        self.model_combo.addItem(t('ai_tools.linear_regression'), 'linear_regression')
        self.model_combo.addItem(t('ai_tools.polynomial_regression'), 'polynomial_regression')
        self.model_combo.addItem(t('ai_tools.neural_network'), 'neural_network')

        self.degree_spin = QSpinBox()
        self.degree_spin.setRange(2, 5)
        self.degree_spin.setValue(2)

        self.fit_button = QPushButton(t('ai_tools.fit_data'))
        self.clear_points_button = QPushButton(t('ai_tools.clear_points'))
        self.generate_button = QPushButton(t('ai_tools.generate_random_points'))
        self.points_count_spin = QSpinBox()
        self.points_count_spin.setRange(5, 50)
        self.points_count_spin.setValue(10)

        self.model_type_label = QLabel(t('ai_tools.model_type'))
        self.scatter_layout.addWidget(self.model_type_label)
        self.scatter_layout.addWidget(self.model_combo)

        self.poly_degree_label = QLabel(t('ai_tools.polynomial_degree'))
        self.scatter_layout.addWidget(self.poly_degree_label)
        self.scatter_layout.addWidget(self.degree_spin)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.fit_button)
        button_layout.addWidget(self.clear_points_button)
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.points_count_spin)
        self.scatter_layout.addLayout(button_layout)

        self.result_label = QLabel(t('ai_tools.result'))
        self.scatter_layout.addWidget(self.result_label)

        self.equation_label = QLabel()
        self.equation_label.setStyleSheet('font-family: serif; font-size: 14px;')
        self.scatter_layout.addWidget(self.equation_label)

        self.mse_label = QLabel()
        self.scatter_layout.addWidget(self.mse_label)

        self.tab_widget.addTab(self.scatter_tab, t('ai_tools.scatter_fitting'))

        # ------------------------------------------------------------------
        # Tab 1: Digit Recognition
        # ------------------------------------------------------------------
        self.digit_tab = QWidget()
        self.digit_layout = QVBoxLayout(self.digit_tab)

        self.drawing_view = QGraphicsView()
        self.drawing_scene = QGraphicsScene()
        self.drawing_view.setScene(self.drawing_scene)
        self.drawing_view.setFixedSize(280, 280)
        self.drawing_view.setStyleSheet('background-color: white; border: 1px solid #c3c6d7;')

        self.drawing_points = []

        self.recognize_button = QPushButton(t('ai_tools.recognize_digit'))
        self.clear_drawing_button = QPushButton(t('ai_tools.clear_drawing'))

        self.digit_layout.addWidget(self.drawing_view)
        self.digit_layout.addWidget(self.recognize_button)
        self.digit_layout.addWidget(self.clear_drawing_button)

        self.result_digit_label = QLabel(t('ai_tools.prediction'))
        self.digit_layout.addWidget(self.result_digit_label)

        self.top3_label = QLabel()
        self.digit_layout.addWidget(self.top3_label)

        self.tab_widget.addTab(self.digit_tab, t('ai_tools.digit_recognition'))

        # ------------------------------------------------------------------
        # Tab 2: Clustering
        # ------------------------------------------------------------------
        self.cluster_tab = QWidget()
        self.cluster_layout = QVBoxLayout(self.cluster_tab)

        self.cluster_method_combo = QComboBox()
        self.cluster_method_combo.addItem(t('ai_tools.kmeans'), 'k-means')
        self.cluster_method_combo.addItem(t('ai_tools.dbscan'), 'dbscan')

        self.cluster_count_spin = QSpinBox()
        self.cluster_count_spin.setRange(2, 10)
        self.cluster_count_spin.setValue(3)

        self.cluster_button = QPushButton(t('ai_tools.run_clustering'))

        self.cluster_method_label = QLabel(t('ai_tools.method'))
        self.cluster_layout.addWidget(self.cluster_method_label)
        self.cluster_layout.addWidget(self.cluster_method_combo)

        self.cluster_count_label = QLabel(t('ai_tools.number_of_clusters'))
        self.cluster_layout.addWidget(self.cluster_count_label)
        self.cluster_layout.addWidget(self.cluster_count_spin)
        self.cluster_layout.addWidget(self.cluster_button)

        self.cluster_result_label = QLabel()
        self.cluster_layout.addWidget(self.cluster_result_label)

        self.tab_widget.addTab(self.cluster_tab, t('ai_tools.clustering'))

        # ------------------------------------------------------------------
        # Tab 3: Training Notebook
        # ------------------------------------------------------------------
        self.training_tab = QWidget()
        self.training_layout = QVBoxLayout(self.training_tab)

        self.code_editor = AutocompleteTextEdit()
        self.code_editor.setPlaceholderText(t('ai_tools.write_training_code'))
        self.code_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)

        self.run_button = QPushButton(t('ai_tools.run_training'))
        self.stop_training_button = QPushButton(t('ai_tools.stop'))

        self.progress_bar = QProgressBar()

        self.output_area = QPlainTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)

        self.training_layout.addWidget(self.code_editor)
        self.training_layout.addWidget(self.run_button)
        self.training_layout.addWidget(self.stop_training_button)
        self.training_layout.addWidget(self.progress_bar)
        self.training_layout.addWidget(self.output_area)

        self.tab_widget.addTab(self.training_tab, t('ai_tools.training_notebook'))

        # ------------------------------------------------------------------
        # Tab 4: AI Assistant Chat
        # ------------------------------------------------------------------
        self.assistant_tab = QWidget()
        self.assistant_layout = QVBoxLayout(self.assistant_tab)

        self.chat_display = QTextBrowser()
        self.chat_display.setReadOnly(True)
        self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                color: #1a1a2e;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                border: 1px solid #e0e4e8;
                border-radius: 4px;
            }
        """)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText(t('ai_tools.ask_question'))
        self.chat_input.returnPressed.connect(self.on_send_message)

        self.send_button = QPushButton(t('ai_tools.send'))
        self.send_button.clicked.connect(self.on_send_message)

        self.provider_combo = QComboBox()
        self.provider_combo.addItem('Local Demo', AIProvider.LOCAL.value)
        self.provider_combo.addItem('OpenAI', AIProvider.OPENAI.value)
        self.provider_combo.addItem('Claude', AIProvider.CLAUDE.value)
        self.provider_combo.addItem('Gemini', AIProvider.GEMINI.value)
        self.provider_combo.addItem('DeepSeek', AIProvider.DEEPSEEK.value)
        self.provider_combo.addItem('Kimi', AIProvider.KIMI.value)
        self.provider_combo.addItem('Minimax', AIProvider.MINIMAX.value)
        self.provider_combo.addItem('Qwen (通义千问)', AIProvider.QWEN.value)
        self.provider_combo.addItem('Zhipu (智谱清言)', AIProvider.ZHIPU.value)
        self.provider_combo.addItem('Doubao (豆包)', AIProvider.DOUBAO.value)
        self.provider_combo.addItem('Ollama', AIProvider.OLLAMA.value)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.send_button)

        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel(t('ai_tools.provider')))
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addStretch()

        self.assistant_layout.addLayout(provider_layout)
        self.assistant_layout.addWidget(self.chat_display)
        self.assistant_layout.addLayout(input_layout)

        self.tab_widget.addTab(self.assistant_tab, t('ai_tools.ai_assistant'))

        # ------------------------------------------------------------------
        self.layout.addWidget(self.tab_widget)
        self.setWidget(self.widget)

        # Signal connections
        self.fit_button.clicked.connect(self.on_fit)
        self.clear_points_button.clicked.connect(self.on_clear_points)
        self.generate_button.clicked.connect(self.on_generate_points)
        self.recognize_button.clicked.connect(self.on_recognize)
        self.clear_drawing_button.clicked.connect(self.on_clear_drawing)
        self.cluster_button.clicked.connect(self.on_cluster)
        self.run_button.clicked.connect(self.on_run_training)
        self.stop_training_button.clicked.connect(self.on_stop_training)

        self.drawing_view.mousePressEvent = self.on_drawing_press
        self.drawing_view.mouseMoveEvent = self.on_drawing_move

        self.scatter_points = []

    # ------------------------------------------------------------------
    # i18n
    # ------------------------------------------------------------------
    def retranslate_ui(self):
        self.setWindowTitle(t('ai_tools.title'))

        # Tab titles
        self.tab_widget.setTabText(0, t('ai_tools.scatter_fitting'))
        self.tab_widget.setTabText(1, t('ai_tools.digit_recognition'))
        self.tab_widget.setTabText(2, t('ai_tools.clustering'))
        self.tab_widget.setTabText(3, t('ai_tools.training_notebook'))

        # Scatter tab
        self.model_type_label.setText(t('ai_tools.model_type'))
        self.model_combo.setItemText(0, t('ai_tools.linear_regression'))
        self.model_combo.setItemText(1, t('ai_tools.polynomial_regression'))
        self.model_combo.setItemText(2, t('ai_tools.neural_network'))
        self.poly_degree_label.setText(t('ai_tools.polynomial_degree'))
        self.fit_button.setText(t('ai_tools.fit_data'))
        self.clear_points_button.setText(t('ai_tools.clear_points'))
        self.generate_button.setText(t('ai_tools.generate_random_points'))
        self.result_label.setText(t('ai_tools.result'))

        # Digit tab
        self.recognize_button.setText(t('ai_tools.recognize_digit'))
        self.clear_drawing_button.setText(t('ai_tools.clear_drawing'))
        self.result_digit_label.setText(t('ai_tools.prediction'))

        # Cluster tab
        self.cluster_method_label.setText(t('ai_tools.method'))
        self.cluster_method_combo.setItemText(0, t('ai_tools.kmeans'))
        self.cluster_method_combo.setItemText(1, t('ai_tools.dbscan'))
        self.cluster_count_label.setText(t('ai_tools.number_of_clusters'))
        self.cluster_button.setText(t('ai_tools.run_clustering'))

        # Training tab
        self.code_editor.setPlaceholderText(t('ai_tools.write_training_code'))
        self.run_button.setText(t('ai_tools.run_training'))
        self.stop_training_button.setText(t('ai_tools.stop'))

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------
    def on_fit(self):
        # Use stored userData key instead of parsing display text
        model_type = self.model_combo.currentData()

        if model_type == 'polynomial_regression':
            params = {'degree': self.degree_spin.value()}
        else:
            params = {}

        self.fit_requested.emit(self.scatter_points, model_type, params)

    def on_clear_points(self):
        self.scatter_points.clear()
        self.equation_label.clear()
        self.mse_label.clear()

    def on_generate_points(self):
        n = self.points_count_spin.value()
        self.generate_points.emit(n)

    def on_recognize(self):
        image_data = self.get_drawing_data()
        self.recognize_requested.emit(image_data)

    def on_clear_drawing(self):
        self.drawing_scene.clear()
        self.drawing_points.clear()

    def on_cluster(self):
        # Use stored userData key instead of parsing display text
        method = self.cluster_method_combo.currentData()
        params = {'n_clusters': self.cluster_count_spin.value()}
        self.cluster_requested.emit(self.scatter_points, method, params)

    def on_run_training(self):
        code = self.code_editor.toPlainText()
        if not code.strip():
            return
            
        self.output_area.clear()
        self.output_area.appendPlainText(t('ai_tools.running_training'))
        self.set_loading_state(True)
        
        from PySide6.QtCore import QTimer
        self._training_timer = QTimer(self)
        self._training_timer.setSingleShot(True)
        self._training_timer.timeout.connect(self._finish_training)
        self._training_timer.start(2000)

    def _finish_training(self):
        self.output_area.appendPlainText("Training completed successfully. (Simulated)")
        self.set_loading_state(False)

    def on_stop_training(self):
        if hasattr(self, '_training_timer') and self._training_timer.isActive():
            self._training_timer.stop()
            self.output_area.appendPlainText("Training stopped by user.")
            self.set_loading_state(False)

    def on_drawing_press(self, event):
        scene_pos = self.drawing_view.mapToScene(event.pos())
        self.drawing_points.append((scene_pos.x(), scene_pos.y()))

        dot = QGraphicsEllipseItem(scene_pos.x() - 5, scene_pos.y() - 5, 10, 10)
        dot.setBrush(QBrush(QColor('#0b1c30')))
        self.drawing_scene.addItem(dot)

    def on_drawing_move(self, event):
        if self.drawing_points:
            scene_pos = self.drawing_view.mapToScene(event.pos())
            last_x, last_y = self.drawing_points[-1]

            line = QGraphicsLineItem(last_x, last_y, scene_pos.x(), scene_pos.y())
            line.setPen(QPen(QColor('#0b1c30'), 8))
            self.drawing_scene.addItem(line)

            self.drawing_points.append((scene_pos.x(), scene_pos.y()))

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------
    def get_drawing_data(self, stroke_radius=2):
        data = [[0] * 28 for _ in range(28)]

        for x, y in self.drawing_points:
            grid_x = min(max(0, int(x / 10)), 27)
            grid_y = min(max(0, int(y / 10)), 27)
            
            for dy in range(-stroke_radius, stroke_radius + 1):
                for dx in range(-stroke_radius, stroke_radius + 1):
                    nx = grid_x + dx
                    ny = grid_y + dy
                    if 0 <= nx < 28 and 0 <= ny < 28:
                        distance = (dx ** 2 + dy ** 2) ** 0.5
                        if distance <= stroke_radius:
                            intensity = int(255 * (1 - distance / (stroke_radius + 1)))
                            data[ny][nx] = max(data[ny][nx], intensity)

        return data

    def set_scatter_points(self, points):
        self.scatter_points = points

    def set_fit_result(self, result):
        if result.get('success'):
            self.equation_label.setText(result.get('equation', ''))
            self.mse_label.setText(f'MSE: {result.get("mse", 0):.4f}')

    def set_recognition_result(self, result):
        if result.get('success'):
            self.result_digit_label.setText(
                f'{t("ai_tools.prediction")} {result["prediction"]}'
            )
            top3 = result.get('top3', [])
            top3_text = '\n'.join(
                [f'{item["digit"]}: {item["probability"]:.2%}' for item in top3]
            )
            self.top3_label.setText(f'{t("ai_tools.top3")}\n{top3_text}')

    def set_cluster_result(self, result):
        if result.get('success'):
            self.cluster_result_label.setText(
                f'{t("ai_tools.cluster_count")} {result.get("n_clusters", 0)}'
            )

    def append_training_output(self, text):
        self.output_area.appendPlainText(text)

    def set_loading_state(self, is_loading: bool):
        self.fit_button.setEnabled(not is_loading)
        self.cluster_button.setEnabled(not is_loading)
        self.recognize_button.setEnabled(not is_loading)
        self.generate_button.setEnabled(not is_loading)
        self.run_button.setEnabled(not is_loading)
        self.stop_training_button.setEnabled(is_loading)

    # ------------------------------------------------------------------
    # AI Assistant Chat Methods
    # ------------------------------------------------------------------
    def on_send_message(self):
        user_text = self.chat_input.text().strip()
        if not user_text:
            return

        # 在界面上追加用户消息
        user_html = f"<div style='color: #0078D7; text-align: right;'><b>{t('ai_tools.you')}:</b> {user_text}</div><br>"
        self.chat_display.append(user_html)
        self.chat_display.append(f"<b>🤖 {t('ai_tools.assistant')}:</b> ")

        self.chat_input.clear()
        self.chat_input.setEnabled(False)
        self.send_button.setEnabled(False)
        self.send_button.setText("思考中...")

        # 🚨 1. 提取当前“具身”上下文：活的几何拓扑树
        system_context = self._get_system_context()
        main_win = self.window()
        engine = main_win.geometry_engine if hasattr(main_win, 'geometry_engine') else None
        live_context = ""
        
        if engine:
            import json
            objects = engine.get_all_objects()
            simplified_state = []
            for obj in objects:
                simplified_state.append({
                    "id": obj.id,
                    "type": obj.type,
                    "name": obj.name,
                    "coords": {k: round(v, 3) for k, v in obj.coordinates.items() if isinstance(v, (int, float))}
                })
            
            if simplified_state:
                live_context = f"\n[系统后台自动附加] 当前 2D/3D 画布状态:\n{json.dumps(simplified_state, ensure_ascii=False)}"

        enhanced_prompt = user_text + live_context
        
        sys_prompt = "你是一个名为 MathLab 的高级数学与编程助教。请尽量使用清晰的 Markdown 格式回答。遇到公式请使用 LaTeX。对于代码解释尽量详细且易懂。\n" + NL2DRAW_SYSTEM_PROMPT
        if system_context:
            import json
            sys_prompt += f"\n系统上下文: {json.dumps(system_context, ensure_ascii=False)}"
            
        self._current_response = ""
        
        if hasattr(main_win, 'ai_manager'):
            main_win.ai_manager.ask(
                user_prompt=enhanced_prompt,
                system_prompt=sys_prompt,
                history=[],
                on_chunk=self.on_chunk_received,
                on_finish=self.on_request_finished,
                on_error=self.on_request_error
            )
            self.breath_anim = start_breathing_effect(self.send_button)
        else:
            self.on_request_error("AIManager 未初始化！")

    def _get_system_context(self):
        system_context = {}
        main_win = self.window()
        
        if hasattr(main_win, 'geometry_engine'):
            try:
                system_context['geometry'] = main_win.geometry_engine.serialize_all()
            except Exception:
                system_context['geometry'] = {}
        
        if hasattr(main_win, 'cas_provider'):
            system_context['cas_enabled'] = True
        
        return system_context

    def on_chunk_received(self, text_chunk: str):
        self._current_response += text_chunk
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text_chunk)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def on_action_required(self, action_data: dict):
        self.action_requested.emit(action_data)

    def on_request_finished(self):
        self.chat_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.send_button.setText(t('ai_tools.send'))
        self.chat_input.setFocus()
        
        if hasattr(self, 'breath_anim'):
            self.breath_anim.stop()
            try:
                from ..ui.animations import get_opacity_effect
            except ImportError as e:
                from ui.animations import get_opacity_effect
            get_opacity_effect(self.send_button).setOpacity(1.0)
            
        self.parse_and_execute_draw_commands(self._current_response)
        
        # 将 JSON 块在渲染前抹掉
        cleaned_response = re.sub(r'```json\s*\[\s*\{.*?\}\s*\]\s*```', '', self._current_response, flags=re.DOTALL | re.IGNORECASE)
            
        # 重新渲染为 Markdown
        final_html = markdown.markdown(cleaned_response, extensions=['fenced_code', 'tables'])
        
        self.chat_display.append("<br><hr>")
        
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def parse_and_execute_draw_commands(self, text):
        match = re.search(r'```json\s*(\[\s*\{.*?\}\s*\])\s*```', text, flags=re.DOTALL | re.IGNORECASE)
        if match:
            json_str = match.group(1)
            try:
                import json
                commands = json.loads(json_str)
                main_window = self.window()
                if hasattr(main_window, 'geometry_engine'):
                    self._execute_geometry_commands(main_window.geometry_engine, commands)
                    self.chat_display.append("<i style='color: #27AE60;'>✨ 魔法触发：已自动为您绘制该图形！</i>")
            except Exception as e:
                print(f"NL2Draw JSON 解析或执行失败: {e}")

    def _execute_geometry_commands(self, engine, commands: list):
        for cmd in commands:
            op = cmd.get("cmd")
            # 兼容防幻觉重命名
            if op == "draw_point": op = "add_point"
            if op == "draw_circle": op = "add_circle"
            if op == "draw_segment": op = "add_segment"
            if op == "draw_polygon": op = "add_polygon"
            
            try:
                if op == "add_point":
                    engine.add_point(cmd.get("x", 0), cmd.get("y", 0), cmd.get("name"))
                elif op == "add_circle":
                    engine.add_circle(cmd["center"], cmd.get("radius", 1))
                elif op == "add_polygon":
                    engine.add_polygon(cmd["points"])
                elif op == "add_segment":
                    engine.add_segment(cmd["p1"], cmd["p2"])
            except Exception as e:
                print(f"执行指令 {op} 失败: {e}")

    def on_request_error(self, error_msg: str):
        self.chat_display.append(f"<span style='color: #dc2626;'><b>❌ {t('ai_tools.error')}:</b> {error_msg}</span><hr>")
        self.chat_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.send_button.setText(t('ai_tools.send'))
        if hasattr(self, 'breath_anim'):
            self.breath_anim.stop()
            try:
                from ..ui.animations import get_opacity_effect
            except ImportError as e:
                from ui.animations import get_opacity_effect
            get_opacity_effect(self.send_button).setOpacity(1.0)

