from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QComboBox, QSpinBox,
    QLabel, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsLineItem,
    QProgressBar, QPlainTextEdit
)
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtCore import Qt, Signal

try:
    from ..utils.i18n_manager import t
except ImportError:
    from utils.i18n_manager import t


class AIToolsPanel(QDockWidget):
    fit_requested = Signal(list, str)
    cluster_requested = Signal(list, str, dict)
    recognize_requested = Signal(list)
    generate_points = Signal(int)

    def __init__(self, parent=None):
        super().__init__(t('ai_tools.title'), parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea)

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

        self.code_editor = QPlainTextEdit()
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

        self.fit_requested.emit(self.scatter_points, model_type)

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
        code = self.code_editor.toPlainText()  # noqa: F841
        self.output_area.appendPlainText(t('ai_tools.running_training'))

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
    def get_drawing_data(self):
        data = [[0] * 28 for _ in range(28)]

        for x, y in self.drawing_points:
            grid_x = min(max(0, int(x / 10)), 27)
            grid_y = min(max(0, int(y / 10)), 27)
            data[grid_y][grid_x] = 255

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
