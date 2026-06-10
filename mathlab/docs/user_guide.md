# MathLab User Guide

## Introduction

Welcome to MathLab, an interactive mathematics and AI teaching software. MathLab combines dynamic geometry, symbolic computation, Python scripting, and AI-powered tools in one comprehensive platform.

---

## Getting Started

### System Requirements

- Windows 10/11 or macOS 10.15+
- Python 3.10 or higher
- 4GB RAM minimum (8GB recommended)
- GPU recommended for AI features

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run MathLab
cd mathlab
python main.py
```

---

## Interface Overview

### Main Window Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ File  Edit  View  Tools  Help                                   │  ← Menu Bar
├─────────────────────────────────────────────────────────────────┤
│ [Select] [Point] [Segment] [Circle] [Polygon] [Pan]            │  ← Toolbar
├──────┬───────────────────────────────────────┬─────────────────┤
│      │                                       │                 │
│      │                                       │                 │
│      │         Geometry Canvas               │                 │
│      │                                       │   Properties    │
│      │     (Main Working Area)               │     Panel       │
│ Algebra                                      │                 │
│ Panel                                        │                 │
│      │                                       │                 │
│      │                                       │                 │
├──────┴───────────────────────────────────────┴─────────────────┤
│                    Python Console                               │  ← Bottom Panel
└─────────────────────────────────────────────────────────────────┘
```

### Toolbar Tools

| Tool | Icon | Description |
|------|------|-------------|
| **Select** | ◉ | Select and move objects |
| **Point** | ● | Add a point to canvas |
| **Segment** | ─ | Add a line segment |
| **Circle** | ○ | Add a circle |
| **Polygon** | ▲ | Add a polygon |
| **Pan** | 🖱 | Pan the canvas |
| **Zoom In** | + | Zoom in |
| **Zoom Out** | - | Zoom out |

---

## Basic Operations

### Drawing Points

1. Click the **Point** tool in the toolbar
2. Click anywhere on the canvas to add a point
3. Points will be labeled automatically (A, B, C, ...)

### Drawing Segments

1. Click the **Segment** tool
2. Click two points on the canvas to connect them
3. The segment will be created between the points

### Drawing Circles

1. Click the **Circle** tool
2. Click a point for the center
3. Click another point to set the radius, or enter radius value in properties panel

### Drawing Polygons

1. Click the **Polygon** tool
2. Click multiple points on the canvas
3. Right-click to complete the polygon

### Selecting and Moving Objects

1. Click the **Select** tool
2. Click an object to select it
3. Drag the object to move it
4. Hold **Shift** to select multiple objects

### Deleting Objects

1. Select the object(s)
2. Press **Delete** key or click **Edit > Delete**

---

## Algebra Panel

The Algebra Panel displays all geometric objects on the canvas with their properties:

- **Name**: Object label (e.g., A, B, segment1)
- **Type**: Point, Segment, Circle, or Polygon
- **Value**: Coordinates or defining properties

Double-click an object name to rename it.

---

## Properties Panel

The Properties Panel shows detailed information about selected objects:

### Point Properties
- **Name**: Editable label
- **Type**: Point
- **X, Y**: Coordinates (editable)
- **Radius**: Display size on canvas

### Circle Properties
- **Name**: Editable label
- **Type**: Circle
- **Center**: Center point
- **Radius**: Circle radius

Click **Apply Changes** to update the object.

---

## Python Console

The Python Console allows you to interact with MathLab using Python code.

### Basic Commands

```python
# Draw a point at coordinates (100, 100)
draw_point(100, 100)

# Solve an equation
solve("x^2 - 4 = 0", "x")

# Simplify expression
simplify("x^2 + 2*x + 1")

# Clear the canvas
clear_canvas()
```

### Available Functions

| Function | Description | Example |
|----------|-------------|---------|
| `draw_point(x, y)` | Draw a point | `draw_point(50, 50)` |
| `draw_segment(p1, p2)` | Draw segment between points | `draw_segment('A', 'B')` |
| `draw_circle(center, radius)` | Draw a circle | `draw_circle('A', 50)` |
| `clear_canvas()` | Clear all objects | `clear_canvas()` |
| `solve(expr, var)` | Solve equation | `solve("x^2=4", "x")` |
| `simplify(expr)` | Simplify expression | `simplify("2*x + x")` |
| `integrate(expr, var)` | Integrate | `integrate("x^2", "x")` |
| `differentiate(expr, var)` | Differentiate | `differentiate("sin(x)", "x")` |
| `limit(expr, var, point)` | Compute limit | `limit("1/x", "x", 0)` |

### Tips

- Press **Enter** to execute code
- Type `%help` for available commands
- Use `app` to access the main window

---

## AI Tools Panel

The AI Tools Panel provides machine learning capabilities:

### Scatter Fitting

1. Go to **AI Tools > Scatter Fitting**
2. Click **Generate Random Points** or manually add points
3. Select a model type:
   - **Linear Regression**: Fits a straight line
   - **Polynomial Regression**: Fits a polynomial curve
   - **Neural Network**: Uses neural network for fitting
4. Click **Fit Data**
5. View the result equation and MSE (Mean Squared Error)

### Digit Recognition

1. Go to **AI Tools > Digit Recognition**
2. Draw a digit (0-9) in the drawing area
3. Click **Recognize Digit**
4. View the prediction and top 3 probabilities

### Clustering

1. Go to **AI Tools > Clustering**
2. Generate or add points
3. Select clustering method:
   - **K-means**: Specify number of clusters
   - **DBSCAN**: Density-based clustering
4. Click **Run Clustering**

### AI Assistant

1. Go to **AI Tools > AI Assistant**
2. Select AI provider (Local Demo, Minimax, Kimi, DeepSeek)
3. Type your question in the input box
4. Click **Send**
5. The AI will respond with answers or canvas operations

---

## Algorithm Visualization

1. Go to **Tools > Algorithm Visualization**
2. Select an algorithm from the dropdown
3. Click **Start** to begin animation
4. Use **Pause** and **Step** for detailed viewing

### Supported Algorithms

- **Bubble Sort** - Simple sorting algorithm
- **Quick Sort** - Efficient sorting algorithm
- **Binary Search** - Search in sorted arrays
- **BFS** - Breadth-First Search
- **DFS** - Depth-First Search
- **Dijkstra** - Shortest path algorithm
- **Convex Hull** - Graham scan algorithm
- **K-means** - Clustering visualization

---

## File Operations

### Saving Work

```
File > Save As...
```

Saves your canvas as a `.mathlab` project file.

### Opening Files

```
File > Open...
```

Loads a previously saved project.

### Exporting

- **Export as Image**: `File > Export > Image`
- **Export as LaTeX**: `File > Export > LaTeX`
- **Export as SVG**: `File > Export > SVG`

---

## View Options

### Zooming

- **Zoom In**: `View > Zoom In` or toolbar button
- **Zoom Out**: `View > Zoom Out` or toolbar button
- **Reset Zoom**: `View > Reset Zoom`
- **Fit to Window**: `View > Fit to Window`

### Grid

- **Show Grid**: `View > Show Grid`
- **Grid Size**: `View > Grid Size > [Small/Medium/Large]`

---

## Preferences

### Language Settings

1. `Tools > Preferences`
2. Select language: English or 中文
3. Restart MathLab for changes to take effect

### Theme Settings

1. `Tools > Preferences`
2. Select theme: Light or Dark
3. Click **Apply**

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New project |
| `Ctrl+O` | Open project |
| `Ctrl+S` | Save project |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Delete` | Delete selected |
| `Ctrl++` | Zoom in |
| `Ctrl+-` | Zoom out |
| `Ctrl+0` | Reset zoom |
| `Esc` | Deselect / Cancel |

---

## Tips and Tricks

### Working with Constraints

MathLab supports geometric constraints:
- Points can be constrained to coordinates
- Segments maintain their endpoints
- Circles maintain their center and radius

### Using Python Scripts

You can write scripts to automate tasks:

```python
# Draw a square
p1 = draw_point(0, 0)
p2 = draw_point(100, 0)
p3 = draw_point(100, 100)
p4 = draw_point(0, 100)
draw_segment('point_0', 'point_1')
draw_segment('point_1', 'point_2')
draw_segment('point_2', 'point_3')
draw_segment('point_3', 'point_0')
```

### Troubleshooting

**Issue**: UI becomes unresponsive
- Solution: AI operations run in background. Wait for status bar message.

**Issue**: Cannot draw points
- Solution: Ensure the Point tool is selected

**Issue**: Python console errors
- Solution: Check syntax and function names

---

## Support

If you encounter issues or have questions:

1. Check the **Help > Documentation** menu
2. Visit our GitHub repository for updates
3. Report bugs via GitHub issues

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026 | Initial release |

---

## License

MathLab is released under the MIT License.
