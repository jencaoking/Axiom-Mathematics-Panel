from collections import defaultdict


class DAG:
    """有向无环图：使用 set 存储邻接关系，实现 O(1) 的边添加与节点移除。

    相比旧版基于 list 的实现：
    - add_edge: O(1) 集合插入替代 O(n) 的 `not in` 线性检查
    - remove_node: O(1) 集合 discard 替代 O(n) 的 list.remove
    """

    def __init__(self):
        self.graph = defaultdict(set)
        self.reverse_graph = defaultdict(set)

    def add_edge(self, from_node, to_node):
        if self._is_reachable(to_node, from_node):
            raise ValueError(f"Cycle detected: {from_node} → {to_node}")
        self.graph[from_node].add(to_node)
        self.reverse_graph[to_node].add(from_node)

    def _is_reachable(self, src, dst):
        visited = set()
        stack = [src]
        while stack:
            n = stack.pop()
            if n == dst:
                return True
            if n in visited:
                continue
            visited.add(n)
            stack.extend(self.graph.get(n, ()))
        return False

    def remove_node(self, node):
        for child in self.graph.get(node, ()):
            self.reverse_graph.get(child, set()).discard(node)

        for parent in self.reverse_graph.get(node, ()):
            self.graph.get(parent, set()).discard(node)

        self.graph.pop(node, None)
        self.reverse_graph.pop(node, None)

    def get_dependencies(self, node):
        visited = set()
        visiting = set()
        result = []

        def dfs(n):
            if n in visited:
                return
            if n in visiting:
                raise ValueError(f"Cycle detected at node {n}")
            visiting.add(n)
            for dep in self.reverse_graph.get(n, ()):
                dfs(dep)
            visiting.remove(n)
            visited.add(n)
            result.append(n)

        dfs(node)
        return result

    def get_dependents(self, node):
        """返回所有依赖节点，按拓扑顺序排列（父节点在子节点之前）。

        使用后序遍历的逆序实现严格拓扑排序，确保任意节点都先于
        其下游节点被返回，从而 update_point 中可以安全地按顺序
        更新依赖图，不会出现读取到脏数据的情况。
        """
        visited = set()
        visiting = set()
        result = []

        def dfs(n):
            if n in visited:
                return
            if n in visiting:
                raise ValueError(f"Cycle detected at node {n}")
            visiting.add(n)
            for dep in self.graph.get(n, ()):
                dfs(dep)  # 先深入到底
            visiting.remove(n)
            visited.add(n)
            result.append(n)  # 后序收集

        dfs(node)
        # 逆序得到正确的拓扑顺序
        result.reverse()
        # 移除起始节点自身，调用方只需要依赖项
        return [x for x in result if x != node]
