from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QComboBox, QSpinBox,
    QLabel, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsLineItem,
    QProgressBar, QPlainTextEdit
)
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtCore import Qt, Signal

class AIToolsPanel(QDockWidget):
    fit_requested = Signal(list, str)
    cluster_requested = Signal(list, str, dict)
    recognize_requested = Signal(list)
    generate_points = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__('AI Tools', parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        
        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)
        
        self.tab_widget = QTabWidget()
        
        self.scatter_tab = QWidget()
        self.scatter_layout = QVBoxLayout(self.scatter_tab)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(['Linear Regression', 'Polynomial Regression', 'Neural Network'])
        
        self.degree_spin = QSpinBox()
        self.degree_spin.setRange(2, 5)
        self.degree_spin.setValue(2)
        
        self.fit_button = QPushButton('Fit Data')
        self.clear_points_button = QPushButton('Clear Points')
        self.generate_button = QPushButton('Generate Random Points')
        self.points_count_spin = QSpinBox()
        self.points_count_spin.setRange(5, 50)
        self.points_count_spin.setValue(10)
        
        self.scatter_layout.addWidget(QLabel('Model Type:'))
        self.scatter_layout.addWidget(self.model_combo)
        self.scatter_layout.addWidget(QLabel('Polynomial Degree:'))
        self.scatter_layout.addWidget(self.degree_spin)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.fit_button)
        button_layout.addWidget(self.clear_points_button)
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.points_count_spin)
        self.scatter_layout.addLayout(button_layout)
        
        self.result_label = QLabel('Result:')
        self.scatter_layout.addWidget(self.result_label)
        
        self.equation_label = QLabel()
        self.equation_label.setStyleSheet('font-family: serif; font-size: 14px;')
        self.scatter_layout.addWidget(self.equation_label)
        
        self.mse_label = QLabel()
        self.scatter_layout.addWidget(self.mse_label)
        
        self.tab_widget.addTab(self.scatter_tab, 'Scatter Fitting')
        
        self.digit_tab = QWidget()
        self.digit_layout = QVBoxLayout(self.digit_tab)
        
        self.drawing_view = QGraphicsView()
        self.drawing_scene = QGraphicsScene()
        self.drawing_view.setScene(self.drawing_scene)
        self.drawing_view.setFixedSize(280, 280)
        self.drawing_view.setStyleSheet('background-color: white; border: 1px solid #c3c6d7;')
        
        self.drawing_points = []
        
        self.recognize_button = QPushButton('Recognize Digit')
        self.clear_drawing_button = QPushButton('Clear Drawing')
        
        self.digit_layout.addWidget(self.drawing_view)
        self.digit_layout.addWidget(self.recognize_button)
        self.digit_layout.addWidget(self.clear_drawing_button)
        
        self.result_digit_label = QLabel('Prediction:')
        self.digit_layout.addWidget(self.result_digit_label)
        
        self.top3_label = QLabel()
        self.digit_layout.addWidget(self.top3_label)
        
        self.tab_widget.addTab(self.digit_tab, 'Digit Recognition')
        
        self.cluster_tab = QWidget()
        self.cluster_layout = QVBoxLayout(self.cluster_tab)
        
        self.cluster_method_combo = QComboBox()
        self.cluster_method_combo.addItems(['K-Means', 'DBSCAN'])
        
        self.cluster_count_spin = QSpinBox()
        self.cluster_count_spin.setRange(2, 10)
        self.cluster_count_spin.setValue(3)
        
        self.cluster_button = QPushButton('Run Clustering')
        
        self.cluster_layout.addWidget(QLabel('Method:'))
        self.cluster_layout.addWidget(self.cluster_method_combo)
        self.cluster_layout.addWidget(QLabel('Number of Clusters:'))
        self.cluster_layout.addWidget(self.cluster_count_spin)
        self.cluster_layout.addWidget(self.cluster_button)
        
        self.cluster_result_label = QLabel()
        self.cluster_layout.addWidget(self.cluster_result_label)
        
        self.tab_widget.addTab(self.cluster_tab, 'Clustering')
        
        self.training_tab = QWidget()
        self.training_layout = QVBoxLayout(self.training_tab)
        
        self.code_editor = QPlainTextEdit()
        self.code_editor.setPlaceholderText('Write your training code here...')
        self.code_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)
        
        self.run_button = QPushButton('Run Training')
        self.stop_training_button = QPushButton('Stop')
        
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
        
        self.tab_widget.addTab(self.training_tab, 'Training Notebook')
        
        self.layout.addWidget(self.tab_widget)
        
        self.setWidget(self.widget)
        
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
    
    def on_fit(self):
        model_type = self.model_combo.currentText()
        model_type = model_type.lower().replace(' ', '_')
        
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
        method = self.cluster_method_combo.currentText().lower()
        params = {'n_clusters': self.cluster_count_spin.value()}
        self.cluster_requested.emit(self.scatter_points, method, params)
    
    def on_run_training(self):
        code = self.code_editor.toPlainText()
        self.output_area.appendPlainText('Running training...')
    
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
            self.result_digit_label.setText(f'Prediction: {result["prediction"]}')
            top3 = result.get('top3', [])
            top3_text = '\n'.join([f'{item["digit"]}: {item["probability"]:.2%}' for item in top3])
            self.top3_label.setText(f'Top 3:\n{top3_text}')
    
    def set_cluster_result(self, result):
        if result.get('success'):
            self.cluster_result_label.setText(f'Clusters: {result.get("n_clusters", 0)}')
    
    def append_training_output(self, text):
        self.output_area.appendPlainText(text)
