# MathLab API Documentation

## Overview

MathLab is an interactive mathematics and AI teaching software that provides:
- Dynamic geometry system
- Computer Algebra System (CAS)
- Python scripting environment
- AI-powered tools (regression, clustering, digit recognition)
- Algorithm visualization

---

## Core Modules

### 1. Geometry Engine

#### GeometryEngine Class

```python
class GeometryEngine
```

**Methods:**

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `add_point(x, y, name=None)` | Add a point to the canvas | `x`: float, `y`: float, `name`: str | `point_id`: str |
| `add_segment(point1_id, point2_id)` | Add a line segment | `point1_id`: str, `point2_id`: str | `segment_id`: str |
| `add_circle(center_id, radius)` | Add a circle | `center_id`: str, `radius`: float | `circle_id`: str |
| `add_polygon(point_ids)` | Add a polygon | `point_ids`: list[str] | `polygon_id`: str |
| `update_point(point_id, **kwargs)` | Update point coordinates | `point_id`: str, `x/y`: float | None |
| `remove_object(obj_id)` | Remove an object | `obj_id`: str | None |
| `serialize_all()` | Serialize all objects | None | `dict` |
| `add_listener(callback)` | Add event listener | `callback`: callable | None |

**Events:**
- `object_added`: Emitted when an object is added
- `object_updated`: Emitted when an object is updated
- `object_removed`: Emitted when an object is removed

#### Example Usage

```python
from mathlab.core.geometry_engine import GeometryEngine

engine = GeometryEngine()

# Add points
p1 = engine.add_point(0, 0, name='A')
p2 = engine.add_point(3, 4, name='B')

# Add segment
seg = engine.add_segment(p1, p2)

# Add circle
center = engine.add_point(0, 0)
circle = engine.add_circle(center, radius=5)
```

---

### 2. CAS Provider

#### CASProvider Class

```python
class CASProvider
```

**Methods:**

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `simplify(expr_str)` | Simplify expression | `expr_str`: str | `dict` |
| `expand(expr_str)` | Expand expression | `expr_str`: str | `dict` |
| `factor(expr_str)` | Factor expression | `expr_str`: str | `dict` |
| `differentiate(expr_str, var)` | Differentiate | `expr_str`: str, `var`: str | `dict` |
| `integrate(expr_str, var)` | Integrate | `expr_str`: str, `var`: str | `dict` |
| `limit(expr_str, var, point)` | Compute limit | `expr_str`: str, `var`: str, `point`: float | `dict` |
| `solve_equation(expr_str, var)` | Solve equation | `expr_str`: str, `var`: str | `dict` |

**Return Format:**
```python
{
    "success": bool,
    "latex": str,      # LaTeX representation
    "result": str,     # String result
    "error": str       # Error message (if failed)
}
```

#### Example Usage

```python
from mathlab.core.cas_provider import CASProvider

cas = CASProvider()

# Simplify expression
result = cas.simplify("x^2 + 2*x + 1")
# {"success": true, "latex": "(x+1)^2", "result": "(x + 1)**2"}

# Solve equation
result = cas.solve_equation("x^2 - 4 = 0", "x")
# {"success": true, "result": "[-2, 2]"}

# Compute derivative
result = cas.differentiate("sin(x)", "x")
# {"success": true, "latex": "\\cos\\left(x\\right)", "result": "cos(x)"}
```

---

### 3. AI Manager

#### AIManager Class

```python
class AIManager
```

**Methods:**

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `fit_linear_regression(points)` | Linear regression | `points`: list[(x, y)] | `dict` |
| `fit_polynomial_regression(points, degree)` | Polynomial regression | `points`: list[(x, y)], `degree`: int | `dict` |
| `fit_neural_network(points)` | Neural network fitting | `points`: list[(x, y)] | `dict` |
| `cluster_kmeans(points, n_clusters)` | K-means clustering | `points`: list[(x, y)], `n_clusters`: int | `dict` |
| `cluster_dbscan(points)` | DBSCAN clustering | `points`: list[(x, y)] | `dict` |
| `recognize_digit(image_data)` | Digit recognition | `image_data`: list | `dict` |
| `generate_random_points(n, x_range, y_range)` | Generate random points | `n`: int, `x_range/y_range`: tuple | `dict` |

**Return Format (Regression):**
```python
{
    "success": bool,
    "equation": str,   # Fitted equation
    "mse": float,      # Mean squared error
    "params": dict     # Model parameters
}
```

**Return Format (Clustering):**
```python
{
    "success": bool,
    "n_clusters": int,  # Number of clusters
    "labels": list,     # Cluster labels
    "centers": list     # Cluster centers (K-means only)
}
```

#### Example Usage

```python
from mathlab.core.ai_manager import AIManager

ai = AIManager()

# Generate random points
points = ai.generate_random_points(50, x_range=(-10, 10), y_range=(-10, 10))

# Linear regression
result = ai.fit_linear_regression(points['points'])
print(f"Equation: {result['equation']}")

# K-means clustering
result = ai.cluster_kmeans(points['points'], n_clusters=3)
print(f"Clusters: {result['n_clusters']}")
```

---

### 4. Python REPL

#### PythonREPL Class

```python
class PythonREPL
```

**Methods:**

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `execute(code)` | Execute Python code | `code`: str | `dict` |
| `update_namespace(vars)` | Update namespace | `vars`: dict | None |
| `get_namespace()` | Get current namespace | None | `dict` |

**Return Format:**
```python
{
    "success": bool,
    "output": str,   # Output text
    "error": str,    # Error message
    "more": bool     # More output available
}
```

**Predefined Functions:**
- `draw_point(x, y)` - Draw a point on canvas
- `draw_segment(p1, p2)` - Draw a segment
- `draw_circle(center, radius)` - Draw a circle
- `clear_canvas()` - Clear canvas
- `solve(expr, var)` - Solve equation
- `simplify(expr)` - Simplify expression
- `integrate(expr, var)` - Integrate
- `differentiate(expr, var)` - Differentiate
- `limit(expr, var, point)` - Compute limit

---

### 5. Algorithm Animator

#### AlgoAnimator Class

```python
class AlgoAnimator
```

**Supported Algorithms:**

| Algorithm | Description |
|-----------|-------------|
| `bubble_sort` | Bubble sort visualization |
| `quick_sort` | Quick sort visualization |
| `binary_search` | Binary search visualization |
| `bfs` | Breadth-first search |
| `dfs` | Depth-first search |
| `dijkstra` | Dijkstra's algorithm |
| `convex_hull` | Convex hull (Andrew's monotone chain) |
| `kmeans` | K-means clustering animation |

**Methods:**

| Method | Description | Parameters |
|--------|-------------|------------|
| `animate(algorithm, data)` | Start animation | `algorithm`: str, `data`: list |
| `stop()` | Stop animation | None |
| `step()` | Single step | None |
| `reset()` | Reset animation | None |

**Events:**
- `step_ready`: Emitted when a new step is ready

---

### 6. Async Workers

#### Worker Classes

| Class | Purpose | Signals |
|-------|---------|---------|
| `AIFitWorker` | Regression fitting | `finished`, `error` |
| `AIClusterWorker` | Clustering | `finished`, `error` |
| `AIRecognizeWorker` | Digit recognition | `finished`, `error` |
| `AIGeneratePointsWorker` | Point generation | `finished`, `error` |
| `SandboxWorker` | Code execution | `finished`, `error`, `output` |

**Usage Pattern:**

```python
from mathlab.core.async_workers import AIFitWorker

worker = AIFitWorker(ai_manager, points, 'linear_regression')
worker.finished.connect(on_finished)
worker.error.connect(on_error)
worker.start()
```

---

## UI Components

### MainWindow

**Properties:**
- `geometry_engine`: GeometryEngine instance
- `cas_provider`: CASProvider instance
- `ai_manager`: AIManager instance
- `python_repl`: PythonREPL instance
- `central_widget`: GeometryCanvas
- `algebra_panel`: AlgebraPanel
- `ai_tools_panel`: AIToolsPanel

**Methods:**
- `connect_signals()`: Connect all signals
- `execute_ai_action(action_data)`: Execute AI commands
- `on_point_added(x, y, name)`: Handle point creation

---

## Error Handling

All methods return a dictionary with `success` key:

```python
# Success
{"success": True, "result": ...}

# Failure
{"success": False, "error": "Error message"}
```

---

## Version History

| Version | Changes | Date |
|---------|---------|------|
| 1.0.0 | Initial release | 2026 |

---

## License

MIT License
