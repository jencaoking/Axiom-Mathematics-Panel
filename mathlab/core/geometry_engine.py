import uuid
import numpy as np
from typing import List, Callable, Dict, Any

class GeoEntity:
    """几何实体的基类 (节点)"""
    def __init__(self, name: str):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.parents: List['GeoEntity'] = []  # 依赖的父节点 (比如交点依赖于两条直线)
        self.children: List['GeoEntity'] = [] # 依赖于我的子节点
        self.is_visible = True
        self.color = "#007acc"

    def add_child(self, child: 'GeoEntity'):
        if child not in self.children:
            self.children.append(child)

    def update(self):
        """核心方法：当父节点发生变化时，重新计算自身的值，并递归通知子节点"""
        self.compute()
        for child in self.children:
            child.update()

    def compute(self):
        """由子类实现具体的计算逻辑"""
        pass

# ──────────────────────────────────────────────────────────
# 具体几何图元
# ──────────────────────────────────────────────────────────

class GeoPoint(GeoEntity):
    """
    点分为两种：
    1. 自由点 (Free Point)：没有 parents，直接由坐标 (x, y) 定义，用户可任意拖动。
    2. 约束点 (Dependent Point)：有 parents，例如“线段的中点”或“两线的交点”，不可自由拖动。
    """
    def __init__(self, name: str, x: float = 0.0, y: float = 0.0, 
                 compute_fn: Callable = None, parents: List[GeoEntity] = None):
        super().__init__(name)
        self.x = x
        self.y = y
        self.compute_fn = compute_fn # 如果是依赖点，这里存放计算逻辑
        
        if parents:
            self.parents = parents
            for p in parents:
                p.add_child(self)
            self.color = "#4EC9B0" # 约束点用不同的颜色区分 (例如青色)

    def compute(self):
        # 如果这是一个受约束的点，根据父节点重新计算坐标
        if self.compute_fn and self.parents:
            self.x, self.y = self.compute_fn(self.parents)

    def set_coords(self, x: float, y: float):
        """UI 拖动自由点时调用"""
        if self.parents:
            return # 约束点不允许直接拖动修改坐标
        self.x = x
        self.y = y
        self.update() # 坐标改变，通知所有依赖它的子节点更新！

class GeoLine(GeoEntity):
    """通过两点确定的直线/线段"""
    def __init__(self, name: str, p1: GeoPoint, p2: GeoPoint, is_segment: bool = True):
        super().__init__(name)
        self.is_segment = is_segment
        self.parents = [p1, p2]
        p1.add_child(self)
        p2.add_child(self)
        self.color = "#d4d4d4"
        
        # 内部状态
        self.start = (0.0, 0.0)
        self.end = (0.0, 0.0)
        self.compute() # 初始化时计算一次

    def compute(self):
        # 线的位置完全由两个父节点决定
        p1, p2 = self.parents
        self.start = (p1.x, p1.y)
        self.end = (p2.x, p2.y)

# ──────────────────────────────────────────────────────────
# 引擎外观管理器 (Facade)
# ──────────────────────────────────────────────────────────

class GeometryEngine:
    """几何引擎大管家，管理所有实体和拓扑结构"""
    def __init__(self):
        self.entities: Dict[str, GeoEntity] = {}
        self.cas_provider = None

    def set_cas_provider(self, cas_provider):
        self.cas_provider = cas_provider

    def add_free_point(self, name: str, x: float, y: float) -> GeoPoint:
        pt = GeoPoint(name, x, y)
        self.entities[pt.id] = pt
        return pt

    def add_midpoint(self, name: str, p1: GeoPoint, p2: GeoPoint) -> GeoPoint:
        """定义一个约束点：两点的中点"""
        def calc_midpoint(parents: List[GeoPoint]):
            return (parents[0].x + parents[1].x) / 2.0, (parents[0].y + parents[1].y) / 2.0
        
        pt = GeoPoint(name, compute_fn=calc_midpoint, parents=[p1, p2])
        pt.compute() # 立刻计算出初始位置
        self.entities[pt.id] = pt
        return pt

    def add_segment(self, name: str, p1: GeoPoint, p2: GeoPoint) -> GeoLine:
        line = GeoLine(name, p1, p2, is_segment=True)
        self.entities[line.id] = line
        return line
