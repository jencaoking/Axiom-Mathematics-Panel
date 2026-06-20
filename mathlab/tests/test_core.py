import unittest
import os
import sys
import tempfile
import shutil
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mathlab.core.geometry_engine import GeometryEngine, Point, Segment, Circle, Polygon, DAG, GeometricObject
from mathlab.core.cas_provider import CASProvider
from mathlab.core.python_repl import PythonREPL
from mathlab.core.algo_animator import AlgoAnimator
from mathlab.core.sandbox import SandboxProcess, SandboxManager
from mathlab.core.ai_manager import AIManager
from mathlab.data.file_manager import FileManager, FileCategory, SearchFilter, FileIndex
from mathlab.utils.latex_renderer import export_canvas_to_latex, format_point, format_segment
from mathlab.utils.helpers import lerp, clamp, distance, midpoint, parse_coordinates, generate_id


class TestGeometryEngine(unittest.TestCase):
    def setUp(self):
        self.engine = GeometryEngine()

    def test_add_point(self):
        point_id = self.engine.add_point(3.0, 4.0, name='A')
        self.assertIsNotNone(point_id)
        self.assertIn(point_id, self.engine.objects)

        point = self.engine.objects[point_id]
        self.assertEqual(point.name, 'A')
        self.assertEqual(point.type, 'Point')
        self.assertEqual(point.coordinates['x'], 3.0)
        self.assertEqual(point.coordinates['y'], 4.0)

    def test_add_segment(self):
        p1_id = self.engine.add_point(0.0, 0.0)
        p2_id = self.engine.add_point(3.0, 4.0)
        seg_id = self.engine.add_segment(p1_id, p2_id)

        segment = self.engine.objects[seg_id]
        self.assertEqual(segment.type, 'Segment')
        self.assertEqual(segment.point1_id, p1_id)
        self.assertEqual(segment.point2_id, p2_id)

    def test_add_circle(self):
        center_id = self.engine.add_point(0.0, 0.0)
        circle_id = self.engine.add_circle(center_id, radius=5.0)

        circle = self.engine.objects[circle_id]
        self.assertEqual(circle.type, 'Circle')
        self.assertEqual(circle.radius, 5.0)

    def test_add_polygon(self):
        p1 = self.engine.add_point(0.0, 0.0)
        p2 = self.engine.add_point(1.0, 0.0)
        p3 = self.engine.add_point(0.5, 1.0)
        poly_id = self.engine.add_polygon([p1, p2, p3])

        polygon = self.engine.objects[poly_id]
        self.assertEqual(polygon.type, 'Polygon')
        self.assertEqual(len(polygon.point_ids), 3)

    def test_remove_object(self):
        p1_id = self.engine.add_point(0.0, 0.0)
        p2_id = self.engine.add_point(1.0, 1.0)
        seg_id = self.engine.add_segment(p1_id, p2_id)

        self.engine.remove_object(p1_id)

        self.assertNotIn(p1_id, self.engine.objects)
        self.assertNotIn(seg_id, self.engine.objects)

    def test_update_point(self):
        point_id = self.engine.add_point(0.0, 0.0)
        self.engine.update_point(point_id, x=5.0, y=10.0)

        point = self.engine.objects[point_id]
        self.assertEqual(point.coordinates['x'], 5.0)
        self.assertEqual(point.coordinates['y'], 10.0)

    def test_get_objects_by_type(self):
        self.engine.add_point(0.0, 0.0)
        self.engine.add_point(1.0, 1.0)
        center_id = self.engine.add_point(0.0, 0.0)
        self.engine.add_circle(center_id, radius=2.0)

        points = self.engine.get_objects_by_type('Point')
        self.assertEqual(len(points), 3)

    def test_serialize_deserialize(self):
        p1 = self.engine.add_point(3.0, 4.0, name='A')
        data = self.engine.serialize_all()

        new_engine = GeometryEngine()
        new_engine.deserialize_all(data)

        self.assertIn(p1, new_engine.objects)
        self.assertEqual(new_engine.objects[p1].name, 'A')


class TestDAG(unittest.TestCase):
    def setUp(self):
        self.dag = DAG()

    def test_add_edge(self):
        self.dag.add_edge('A', 'B')
        self.assertIn('B', self.dag.graph['A'])
        self.assertIn('A', self.dag.reverse_graph['B'])

    def test_remove_node(self):
        self.dag.add_edge('A', 'B')
        self.dag.add_edge('B', 'C')
        self.dag.remove_node('B')

        self.assertNotIn('B', self.dag.graph)
        self.assertNotIn('B', self.dag.reverse_graph)

    def test_get_dependencies(self):
        self.dag.add_edge('A', 'C')
        self.dag.add_edge('B', 'C')
        deps = self.dag.get_dependencies('C')
        self.assertIn('A', deps)
        self.assertIn('B', deps)

    def test_get_dependents(self):
        self.dag.add_edge('A', 'B')
        self.dag.add_edge('A', 'C')
        deps = self.dag.get_dependents('A')
        self.assertIn('B', deps)
        self.assertIn('C', deps)


class TestCASProvider(unittest.TestCase):
    def setUp(self):
        self.cas = CASProvider()

    def test_parse_expression(self):
        result = self.cas.parse_expression('x + 2')
        self.assertIsNotNone(result)

    def test_simplify(self):
        result = self.cas.simplify('x**2 + 2*x**2')
        self.assertTrue(result['success'])
        self.assertIn('x', result['result'])

    def test_solve_equation(self):
        result = self.cas.solve_equation('x**2 - 4 = 0', 'x')
        self.assertTrue(result['success'])

    def test_differentiate(self):
        result = self.cas.differentiate('x**2 + 3*x', 'x')
        self.assertTrue(result['success'])

    def test_integrate(self):
        result = self.cas.integrate('2*x', 'x')
        self.assertTrue(result['success'])

    def test_limit(self):
        result = self.cas.limit('1/x', 'x', 0)
        self.assertTrue(result['success'])


class TestPythonREPL(unittest.TestCase):
    def setUp(self):
        self.repl = PythonREPL(session_mode=False)

    def test_execute_simple(self):
        """沙箱模式下执行简单代码"""
        result = self.repl.execute('x = 5')
        self.assertTrue(result['success'])
        # 注意：沙箱模式下不支持持久化变量，因此无法通过 namespace 检查
    
    def test_execute_with_output(self):
        """测试输出捕获"""
        result = self.repl.execute('print("hello")')
        self.assertIn('hello', result['output'])
    
    def test_history(self):
        """测试历史记录"""
        self.repl.execute('x = 1')
        self.repl.execute('y = 2')
        history = self.repl.get_history()
        self.assertEqual(len(history), 2)
    
    def test_sandbox_isolation(self):
        """测试沙箱隔离性：每次执行都是独立环境"""
        result1 = self.repl.execute('a = 10')
        self.assertTrue(result1['success'])
        
        # 第二次执行时，第一次定义的变量 a 不存在
        result2 = self.repl.execute('print(a)')
        self.assertFalse(result2['success'])  # 应该失败，因为 a 未定义
        self.assertIn('name', result2['error'].lower())  # NameError


class TestAlgoAnimator(unittest.TestCase):
    def setUp(self):
        self.animator = AlgoAnimator()

    def test_load_algorithm(self):
        result = self.animator.load_algorithm('bubble_sort', arr=[5, 3, 8, 1])
        self.assertTrue(result)
        self.assertEqual(self.animator.current_algorithm, 'bubble_sort')

    def test_step(self):
        self.animator.load_algorithm('bubble_sort', arr=[5, 3, 8, 1])
        state = self.animator.step()
        self.assertIsNotNone(state)
        self.assertEqual(state['type'], 'sorting')

    def test_reset(self):
        self.animator.load_algorithm('bubble_sort', arr=[5, 3, 8, 1])
        self.animator.step()
        self.animator.reset()
        self.assertIsNone(self.animator.current_state)


class TestSandboxProcess(unittest.TestCase):
    def setUp(self):
        self.sandbox = SandboxProcess()

    def test_run_code_success(self):
        result = self.sandbox.run_code('print("test")', timeout=5)
        self.assertIn('test', result['output'])
    
    def test_sandbox_timeout(self):
        """测试超时终止机制"""
        sandbox = SandboxProcess()
        result = sandbox.run_code("while True: pass", timeout=2)
        self.assertEqual(result['success'], False)
        # 看门狗会触发超时或内存限制
        self.assertTrue(
            'timed out' in result['error'].lower() or 
            'Memory limit' in result['error'] or
            'execution timed out' in result['error'].lower()
        )
    
    def test_sandbox_memory_limit(self):
        """测试内存限制（如果安装了 psutil）"""
        sandbox = SandboxProcess()
        sandbox.max_memory_mb = 50  # 降低阈值以便快速测试
        code = "arr = []\nwhile True:\n    arr.append('X' * 1000000)"
        result = sandbox.run_code(code, timeout=10)
        self.assertEqual(result['success'], False)
        # 应该触发内存限制或超时
        self.assertTrue(
            'Memory limit' in result['error'] or
            'timed out' in result['error'].lower()
        )
    
    def test_sandbox_normal_execution(self):
        """测试正常代码执行"""
        sandbox = SandboxProcess()
        result = sandbox.run_code("print('Hello'); import numpy as np; print(np.array([1,2,3]))")
        self.assertEqual(result['success'], True)
        self.assertIn('Hello', result['output'])
        self.assertIn('[1 2 3]', result['output'])


class TestSandboxManager(unittest.TestCase):
    def setUp(self):
        self.manager = SandboxManager()

    def test_create_sandbox(self):
        sandbox_id = self.manager.create_sandbox()
        self.assertTrue(sandbox_id.startswith('sandbox_'))


class TestAIManager(unittest.TestCase):
    def setUp(self):
        self.ai = AIManager()

    def test_fit_linear_regression(self):
        points = [(1.0, 2.0), (2.0, 4.0), (3.0, 6.0)]
        result = self.ai.fit_linear_regression(points)
        self.assertTrue(result['success'])
        self.assertAlmostEqual(result['slope'], 2.0, places=1)

    def test_fit_polynomial_regression(self):
        points = [(0.0, 0.0), (1.0, 1.0), (2.0, 4.0), (3.0, 9.0)]
        result = self.ai.fit_polynomial_regression(points, degree=2)
        self.assertTrue(result['success'])

    def test_cluster_kmeans(self):
        points = [[1.0, 1.0], [1.5, 2.0], [5.0, 8.0], [8.0, 8.0]]
        result = self.ai.cluster_kmeans(points, n_clusters=2)
        self.assertTrue(result['success'])
        self.assertEqual(len(result['centers']), 2)

    def test_generate_random_points(self):
        result = self.ai.generate_random_points(n=10)
        self.assertTrue(result['success'])
        self.assertEqual(len(result['points']), 10)


class TestFileManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager(base_directory=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_project(self):
        result = self.file_manager.create_project('Test Project', FileCategory.GEOMETRY)
        self.assertTrue(result['success'])
        self.assertTrue(os.path.exists(result['file_path']))

    def test_open_project(self):
        create_result = self.file_manager.create_project('Test Project')
        result = self.file_manager.open_project(create_result['file_path'])
        self.assertTrue(result['success'])

    def test_search_projects(self):
        self.file_manager.create_project('Geometry Project', FileCategory.GEOMETRY)
        self.file_manager.create_project('Algebra Project', FileCategory.ALGEBRA)

        search_filter = SearchFilter()
        search_filter.category = FileCategory.GEOMETRY.value
        results = self.file_manager.search_projects(search_filter)
        self.assertGreaterEqual(len(results), 1)

    def test_get_recent_projects(self):
        self.file_manager.create_project('Recent 1')
        self.file_manager.create_project('Recent 2')
        recent = self.file_manager.get_recent_projects(limit=5)
        self.assertGreaterEqual(len(recent), 2)


class TestSearchFilter(unittest.TestCase):
    def test_matches_query(self):
        filter = SearchFilter()
        filter.query = 'test'
        entry = {'name': 'test_project', 'category': 'geometry'}
        self.assertTrue(filter.matches(entry))

    def test_matches_category(self):
        filter = SearchFilter()
        filter.category = 'geometry'
        entry = {'name': 'test', 'category': 'geometry'}
        self.assertTrue(filter.matches(entry))

    def test_matches_object_types(self):
        filter = SearchFilter()
        filter.object_types = ['Point', 'Circle']
        entry = {'name': 'test', 'object_types': ['Point', 'Segment']}
        self.assertTrue(filter.matches(entry))


class TestLatexRenderer(unittest.TestCase):
    def test_export_canvas_to_latex(self):
        objects = [
            {'type': 'Point', 'name': 'A', 'coordinates': {'x': 1.0, 'y': 2.0}},
            {'type': 'Circle', 'name': 'C', 'coordinates': {'cx': 0.0, 'cy': 0.0, 'r': 5.0}}
        ]
        latex = export_canvas_to_latex(objects)
        self.assertIn(r'\documentclass', latex)
        self.assertTrue(r'\draw' in latex or r'\fill' in latex)

    def test_format_point(self):
        result = format_point('A', 1.0, 2.0)
        self.assertIn('A', result)
        self.assertIn('1', result)

    def test_format_segment(self):
        result = format_segment('AB', 'A', 'B')
        self.assertIn(r'\overline', result)


class TestHelpers(unittest.TestCase):
    def test_lerp_exact_middle(self):
        self.assertEqual(lerp(0, 100, 0.5), 50)

    def test_lerp_at_start(self):
        self.assertEqual(lerp(0, 100, 0), 0)

    def test_lerp_at_end(self):
        self.assertEqual(lerp(0, 100, 1), 100)

    def test_clamp_within_range(self):
        self.assertEqual(clamp(50, 0, 100), 50)

    def test_clamp_above_range(self):
        self.assertEqual(clamp(150, 0, 100), 100)

    def test_clamp_below_range(self):
        self.assertEqual(clamp(-50, 0, 100), 0)

    def test_distance_horizontal(self):
        self.assertEqual(distance((0, 0), (3, 0)), 3.0)

    def test_distance_diagonal(self):
        d = distance((0, 0), (3, 4))
        self.assertAlmostEqual(d, 5.0, places=1)

    def test_midpoint_origin_to_one(self):
        result = midpoint((0, 0), (2, 2))
        self.assertEqual(result, (1.0, 1.0))

    def test_parse_coordinates_simple(self):
        result = parse_coordinates('(1, 2)')
        self.assertEqual(result, (1.0, 2.0))

    def test_generate_id_prefix(self):
        id1 = generate_id('point')
        self.assertTrue(id1.startswith('point_'))

    def test_generate_id_unique(self):
        id1 = generate_id('test')
        id2 = generate_id('test')
        self.assertNotEqual(id1, id2)


class TestGeometricObject(unittest.TestCase):
    def test_point_creation(self):
        point = Point('p1', 'A', 1.0, 2.0)
        self.assertEqual(point.name, 'A')
        self.assertEqual(point.coordinates['x'], 1.0)
        self.assertEqual(point.coordinates['y'], 2.0)

    def test_segment_creation(self):
        seg = Segment('s1', 'AB', 'p1', 'p2')
        self.assertEqual(seg.type, 'Segment')
        self.assertEqual(seg.point1_id, 'p1')
        self.assertEqual(seg.point2_id, 'p2')

    def test_circle_creation(self):
        circle = Circle('c1', 'C', 'p1', 5.0)
        self.assertEqual(circle.type, 'Circle')
        self.assertEqual(circle.radius, 5.0)

    def test_polygon_creation(self):
        poly = Polygon('poly1', 'P', ['p1', 'p2', 'p3'])
        self.assertEqual(poly.type, 'Polygon')
        self.assertEqual(len(poly.point_ids), 3)

    def test_serialize(self):
        point = Point('p1', 'A', 1.0, 2.0)
        data = point.serialize()
        self.assertEqual(data['id'], 'p1')
        self.assertEqual(data['name'], 'A')

    def test_deserialize(self):
        data = {
            'id': 'p1',
            'name': 'A',
            'type': 'Point',
            'coordinates': {'x': 1.0, 'y': 2.0},
            'constraints': [],
            'depends_on': []
        }
        point = GeometricObject.deserialize(data)
        self.assertEqual(point.name, 'A')
        self.assertEqual(point.coordinates['x'], 1.0)


if __name__ == '__main__':
    unittest.main()