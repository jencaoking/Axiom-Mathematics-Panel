import numpy as np

def lerp(a, b, t):
    return a + (b - a) * t

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def distance(p1, p2):
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5

def midpoint(p1, p2):
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

def normalize_vector(v):
    v = np.asarray(v)
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

def format_number(value, decimals=2):
    return f'{value:.{decimals}f}'

def parse_coordinates(text):
    text = text.strip()
    if text.startswith('(') and text.endswith(')'):
        text = text[1:-1]
    parts = text.split(',')
    if len(parts) == 2:
        try:
            return float(parts[0].strip()), float(parts[1].strip())
        except (ValueError, IndexError, TypeError):
            return None
    return None

def generate_id(prefix='obj'):
    import uuid
    return f'{prefix}_{uuid.uuid4().hex[:8]}'
