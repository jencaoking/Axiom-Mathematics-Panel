import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import mean_squared_error
import os

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

class AIManager:
    def __init__(self):
        self.models = {}
        self.sandbox = None
        
    def load_onnx_model(self, model_path, model_name):
        if not ONNX_AVAILABLE:
            return {'success': False, 'error': 'ONNX Runtime not available'}
        
        try:
            import onnxruntime as ort
            session = ort.InferenceSession(model_path)
            self.models[model_name] = {
                'session': session,
                'input_name': session.get_inputs()[0].name,
                'output_name': session.get_outputs()[0].name
            }
            return {'success': True, 'message': f'Model {model_name} loaded successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def predict(self, model_name, input_data):
        if model_name not in self.models:
            return {'success': False, 'error': 'Model not found'}
        
        model = self.models[model_name]
        try:
            input_data = np.array(input_data, dtype=np.float32)
            if len(input_data.shape) == 1:
                input_data = input_data.reshape(1, -1)
            
            result = model['session'].run(
                [model['output_name']],
                {model['input_name']: input_data}
            )
            
            return {'success': True, 'prediction': result[0].tolist()}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def fit_linear_regression(self, points):
        if len(points) < 2:
            return {'success': False, 'error': 'Need at least 2 points'}
        
        X = np.array([[p[0]] for p in points], dtype=np.float32)
        y = np.array([p[1] for p in points], dtype=np.float32)
        
        model = LinearRegression()
        model.fit(X, y)
        
        slope = float(model.coef_[0])
        intercept = float(model.intercept_)
        
        predictions = model.predict(X)
        mse = float(mean_squared_error(y, predictions))
        
        return {
            'success': True,
            'slope': slope,
            'intercept': intercept,
            'equation': f'y = {slope:.4f}x + {intercept:.4f}',
            'mse': mse,
            'predictions': predictions.tolist()
        }
    
    def fit_polynomial_regression(self, points, degree=2):
        if len(points) < degree + 1:
            return {'success': False, 'error': f'Need at least {degree + 1} points'}
        
        X = np.array([p[0] for p in points], dtype=np.float64)
        y = np.array([p[1] for p in points], dtype=np.float64)
        
        coefficients = np.polyfit(X, y, degree)[::-1]
        poly = np.poly1d(coefficients[::-1])
        
        predictions = poly(X)
        mse = float(mean_squared_error(y, predictions))
        
        equation = 'y = ' + str(poly)
        
        return {
            'success': True,
            'coefficients': coefficients.tolist(),
            'intercept': float(coefficients[-1]),
            'equation': equation,
            'mse': mse,
            'predictions': predictions.tolist()
        }
    
    def fit_neural_network(self, points, epochs=100, hidden_size=10):
        if not TORCH_AVAILABLE:
            return {'success': False, 'error': 'PyTorch not available'}
        
        if len(points) < 2:
            return {'success': False, 'error': 'Need at least 2 points'}
        
        import torch
        import torch.nn as nn
        
        X = torch.tensor([[p[0]] for p in points], dtype=torch.float32)
        y = torch.tensor([[p[1]] for p in points], dtype=torch.float32)
        
        model = nn.Sequential(
            nn.Linear(1, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1)
        )
        
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        
        loss_history = []
        
        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = model(X)
            loss = criterion(outputs, y)
            loss.backward()
            optimizer.step()
            
            loss_history.append(float(loss.item()))
            
            if epoch % 10 == 0:
                pass
        
        with torch.no_grad():
            predictions = model(X).numpy().flatten()
        
        mse = float(mean_squared_error(y.numpy(), predictions.reshape(-1, 1)))
        
        return {
            'success': True,
            'loss_history': loss_history,
            'mse': mse,
            'predictions': predictions.tolist(),
            'epochs': epochs
        }
    
    def cluster_kmeans(self, points, n_clusters=3):
        if len(points) < n_clusters:
            return {'success': False, 'error': 'Not enough points for clusters'}
        
        X = np.array(points, dtype=np.float32)
        
        model = KMeans(n_clusters=n_clusters, n_init=10)
        model.fit(X)
        
        labels = model.labels_.tolist()
        centers = model.cluster_centers_.tolist()
        
        return {
            'success': True,
            'labels': labels,
            'centers': centers,
            'inertia': float(model.inertia_)
        }
    
    def cluster_dbscan(self, points, eps=0.5, min_samples=5):
        if len(points) < min_samples:
            return {'success': False, 'error': 'Not enough points'}
        
        X = np.array(points, dtype=np.float32)
        
        model = DBSCAN(eps=eps, min_samples=min_samples)
        model.fit(X)
        
        labels = model.labels_.tolist()
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        return {
            'success': True,
            'labels': labels,
            'n_clusters': n_clusters,
            'n_noise': list(labels).count(-1)
        }
    
    def recognize_digit(self, image_data):
        if not ONNX_AVAILABLE:
            return {'success': False, 'error': 'ONNX Runtime not available'}
        
        if 'mnist' not in self.models:
            return {'success': False, 'error': 'MNIST model not loaded'}
        
        model = self.models['mnist']
        
        try:
            image_data = np.array(image_data, dtype=np.float32).reshape(1, 1, 28, 28) / 255.0
            
            result = model['session'].run(
                [model['output_name']],
                {model['input_name']: image_data}
            )
            
            predictions = result[0][0]
            top3_indices = np.argsort(predictions)[::-1][:3]
            top3_probs = predictions[top3_indices].tolist()
            top3_digits = top3_indices.tolist()
            
            return {
                'success': True,
                'prediction': int(np.argmax(predictions)),
                'probabilities': predictions.tolist(),
                'top3': [{'digit': d, 'probability': p} for d, p in zip(top3_digits, top3_probs)]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_random_points(self, n=10, x_range=(0, 100), y_range=(0, 100)):
        points = []
        for _ in range(n):
            x = np.random.uniform(x_range[0], x_range[1])
            y = np.random.uniform(y_range[0], y_range[1])
            points.append((x, y))
        return {'success': True, 'points': points}
    
    def run_training_sandbox(self, code):
        from .sandbox import SandboxProcess
        
        sandbox = SandboxProcess()
        result = sandbox.run_code(code)
        return result
