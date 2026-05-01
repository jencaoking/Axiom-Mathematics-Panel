import uuid
from collections import defaultdict
from sympy import symbols, Eq, solve, latex

class GeometricObject:
    TYPES = ['Point', 'Line', 'Circle', 'Segment', 'Polygon', 'Ray', 'Angle']
    
    def __init__(self, obj_id, name, obj_type):
        self.id = obj_id
        self.name = name
        self.type = obj_type
        self.coordinates = {}
        self.symbolic_expr = None
        self.constraints = []
        self.depends_on = []
    
    def update_coordinates(self):
        pass
    
    def to_latex(self):
        if self.type == 'Point':
            x, y = self.coordinates.get('x', 0), self.coordinates.get('y', 0)
            return rf'{self.name} = ({x}, {y})'
        return self.name
    
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'coordinates': self.coordinates,
            'symbolic_expr': str(self.symbolic_expr) if self.symbolic_expr else None,
            'constraints': [str(c) for c in self.constraints],
            'depends_on': self.depends_on
        }
    
    @classmethod
    def deserialize(cls, data):
        obj = cls(data['id'], data['name'], data['type'])
        obj.coordinates = data['coordinates']
        obj.constraints = data.get('constraints', [])
        obj.depends_on = data.get('depends_on', [])
        return obj

class Point(GeometricObject):
    def __init__(self, obj_id, name, x=0, y=0):
        super().__init__(obj_id, name, 'Point')
        self.coordinates = {'x': x, 'y': y}
        self.symbolic_expr = (symbols(f'x_{name}'), symbols(f'y_{name}'))
    
    def update_coordinates(self, x=None, y=None):
        if x is not None:
            self.coordinates['x'] = x
        if y is not None:
            self.coordinates['y'] = y
    
    def to_latex(self):
        x, y = self.coordinates['x'], self.coordinates['y']
        return rf'{self.name} = ({latex(x)}, {latex(y)})'

class Segment(GeometricObject):
    def __init__(self, obj_id, name, point1_id, point2_id):
        super().__init__(obj_id, name, 'Segment')
        self.depends_on = [point1_id, point2_id]
        self.point1_id = point1_id
        self.point2_id = point2_id
    
    def update_coordinates(self, engine):
        p1 = engine.objects.get(self.point1_id)
        p2 = engine.objects.get(self.point2_id)
        if p1 and p2:
            self.coordinates = {
                'x1': p1.coordinates['x'],
                'y1': p1.coordinates['y'],
                'x2': p2.coordinates['x'],
                'y2': p2.coordinates['y']
            }
    
    def to_latex(self):
        return rf'\overline{{{self.name}}}'

class Circle(GeometricObject):
    def __init__(self, obj_id, name, center_id, radius=1.0):
        super().__init__(obj_id, name, 'Circle')
        self.center_id = center_id
        self.radius = radius
        self.depends_on = [center_id]
    
    def update_coordinates(self, engine):
        center = engine.objects.get(self.center_id)
        if center:
            self.coordinates = {
                'cx': center.coordinates['x'],
                'cy': center.coordinates['y'],
                'r': self.radius
            }
    
    def to_latex(self):
        return rf'Circle({self.name})'

class DAG:
    def __init__(self):
        self.graph = defaultdict(list)
        self.reverse_graph = defaultdict(list)
    
    def add_edge(self, from_node, to_node):
        if to_node not in self.graph[from_node]:
            self.graph[from_node].append(to_node)
        if from_node not in self.reverse_graph[to_node]:
            self.reverse_graph[to_node].append(from_node)
    
    def remove_node(self, node):
        for neighbors in self.graph.values():
            if node in neighbors:
                neighbors.remove(node)
        del self.graph[node]
        for parent in self.reverse_graph[node]:
            self.graph[parent].remove(node)
        del self.reverse_graph[node]
    
    def get_dependencies(self, node):
        visited = set()
        result = []
        def dfs(n):
            if n in visited:
                return
            visited.add(n)
            for dep in self.reverse_graph[n]:
                result.append(dep)
                dfs(dep)
        dfs(node)
        return result
    
    def get_dependents(self, node):
        visited = set()
        result = []
        def dfs(n):
            if n in visited:
                return
            visited.add(n)
            for dep in self.graph[n]:
                result.append(dep)
                dfs(dep)
        dfs(node)
        return result

class GeometryEngine:
    def __init__(self):
        self.objects = {}
        self.name_counter = defaultdict(int)
        self.dependencies = DAG()
        self.listeners = []
        self._next_id = 1
    
    def _generate_id(self):
        obj_id = f'obj_{self._next_id}'
        self._next_id += 1
        return obj_id
    
    def _generate_name(self, obj_type):
        prefix = obj_type[0].upper()
        self.name_counter[obj_type] += 1
        return f'{prefix}{self.name_counter[obj_type]}'
    
    def add_listener(self, listener):
        self.listeners.append(listener)
    
    def _notify(self, event_type, data):
        for listener in self.listeners:
            listener(event_type, data)
    
    def add_point(self, x=0, y=0, name=None):
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('Point')
        point = Point(obj_id, name, x, y)
        self.objects[obj_id] = point
        self._notify('object_added', point.serialize())
        return obj_id
    
    def add_segment(self, point1_id, point2_id, name=None):
        if point1_id not in self.objects or point2_id not in self.objects:
            raise ValueError('Points not found')
        
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('Segment')
        segment = Segment(obj_id, name, point1_id, point2_id)
        self.objects[obj_id] = segment
        self.dependencies.add_edge(point1_id, obj_id)
        self.dependencies.add_edge(point2_id, obj_id)
        segment.update_coordinates(self)
        self._notify('object_added', segment.serialize())
        return obj_id
    
    def add_circle(self, center_id, radius=1.0, name=None):
        if center_id not in self.objects:
            raise ValueError('Center point not found')
        
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('Circle')
        circle = Circle(obj_id, name, center_id, radius)
        self.objects[obj_id] = circle
        self.dependencies.add_edge(center_id, obj_id)
        circle.update_coordinates(self)
        self._notify('object_added', circle.serialize())
        return obj_id
    
    def remove_object(self, obj_id):
        if obj_id not in self.objects:
            return
        
        dependents = self.dependencies.get_dependents(obj_id)
        for dep_id in dependents:
            del self.objects[dep_id]
        
        self.dependencies.remove_node(obj_id)
        obj_name = self.objects[obj_id].name
        obj_type = self.objects[obj_id].type
        del self.objects[obj_id]
        
        self.name_counter[obj_type] = max(
            [0] + [int(k[1:]) for k in self.objects.keys() 
                   if self.objects[k].type == obj_type and self.objects[k].name.startswith(obj_type[0])]
        )
        
        self._notify('object_removed', obj_id)
    
    def update_point(self, obj_id, x=None, y=None):
        if obj_id not in self.objects:
            return
        
        point = self.objects[obj_id]
        if x is not None:
            point.coordinates['x'] = x
        if y is not None:
            point.coordinates['y'] = y
        
        dependents = self.dependencies.get_dependents(obj_id)
        for dep_id in dependents:
            dep_obj = self.objects[dep_id]
            dep_obj.update_coordinates(self)
            self._notify('object_updated', dep_obj.serialize())
        
        self._notify('object_updated', point.serialize())
    
    def get_object(self, obj_id):
        return self.objects.get(obj_id)
    
    def get_all_objects(self):
        return list(self.objects.values())
    
    def get_objects_by_type(self, obj_type):
        return [obj for obj in self.objects.values() if obj.type == obj_type]
    
    def solve_constraints(self):
        from scipy.optimize import fsolve
        equations = []
        variables = []
        
        for obj in self.objects.values():
            for constraint in obj.constraints:
                equations.append(constraint)
        
        if equations:
            try:
                result = fsolve(lambda x: [eq.subs(dict(zip(variables, x))) for eq in equations], 
                               [0.0] * len(variables))
                return result
            except:
                return None
        return None
    
    def serialize_all(self):
        return {
            'objects': {obj_id: obj.serialize() for obj_id, obj in self.objects.items()},
            'name_counter': dict(self.name_counter)
        }
    
    def deserialize_all(self, data):
        self.objects.clear()
        self.name_counter = defaultdict(int, data.get('name_counter', {}))
        self.dependencies = DAG()
        
        for obj_id, obj_data in data.get('objects', {}).items():
            obj = GeometricObject.deserialize(obj_data)
            self.objects[obj_id] = obj
            for dep in obj.depends_on:
                self.dependencies.add_edge(dep, obj_id)
        
        for obj in self.objects.values():
            if hasattr(obj, 'update_coordinates'):
                obj.update_coordinates(self)
            self._notify('object_added', obj.serialize())
