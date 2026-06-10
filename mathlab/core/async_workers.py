from PySide6.QtCore import QThread, Signal


class AIFitWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, ai_manager, points, model_type, **kwargs):
        super().__init__()
        self.ai_manager = ai_manager
        self.points = points
        self.model_type = model_type
        self.kwargs = kwargs

    def run(self):
        try:
            if self.model_type == 'neural_network':
                result = self.ai_manager.fit_neural_network(self.points, **self.kwargs)
            elif self.model_type == 'linear_regression':
                result = self.ai_manager.fit_linear_regression(self.points)
            elif self.model_type == 'polynomial_regression':
                degree = self.kwargs.get('degree', 2)
                result = self.ai_manager.fit_polynomial_regression(self.points, degree=degree)
            else:
                result = {"success": False, "error": f"未知的模型类型: {self.model_type}"}

            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AIClusterWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, ai_manager, points, method, params):
        super().__init__()
        self.ai_manager = ai_manager
        self.points = points
        self.method = method
        self.params = params

    def run(self):
        try:
            if self.method == 'k-means':
                n_clusters = self.params.get('n_clusters', 3)
                result = self.ai_manager.cluster_kmeans(self.points, n_clusters=n_clusters)
            else:
                result = self.ai_manager.cluster_dbscan(self.points)

            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AIRecognizeWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, ai_manager, image_data):
        super().__init__()
        self.ai_manager = ai_manager
        self.image_data = image_data

    def run(self):
        try:
            result = self.ai_manager.recognize_digit(self.image_data)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class SandboxWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)
    output = Signal(str)

    def __init__(self, sandbox, code):
        super().__init__()
        self.sandbox = sandbox
        self.code = code

    def run(self):
        try:
            result = self.sandbox.run_code(self.code)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))