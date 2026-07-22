import random
import heapq
from collections import deque

from mathlab.utils.i18n_manager import t

# [P0修复 Bug2] 引入 networkx 并做异常降级处理，防止未安装时整个模块崩溃
try:
    import networkx as nx

    NX_AVAILABLE = True
except ImportError:
    nx = None
    NX_AVAILABLE = False
    print("[Warning] NetworkX is not installed. Graph algorithms (BFS/DFS/Dijkstra) will be disabled.")


class AlgoAnimator:
    def __init__(self):
        self.current_algorithm = None
        self.generator = None
        self.current_state = None
        self.params = {}

    def load_algorithm(self, algorithm_name, **params):
        self.current_algorithm = algorithm_name

        # 为需要随机数据的算法预处理参数，确保 reset() 时可复现
        if algorithm_name == "bubble_sort" or algorithm_name == "quick_sort":
            if "arr" not in params:
                params["arr"] = [random.randint(1, 100) for _ in range(8)]
        elif algorithm_name == "binary_search":
            if "arr" not in params:
                params["arr"] = sorted([random.randint(1, 100) for _ in range(10)])
            if "target" not in params:
                params["target"] = params["arr"][random.randint(0, len(params["arr"]) - 1)]
        elif algorithm_name in ("bfs", "dfs"):
            if "graph" not in params:
                # [P0修复 Bug2] 调用前检查 nx 是否可用
                if not NX_AVAILABLE:
                    return False
                params["graph"] = nx.erdos_renyi_graph(6, 0.5, directed=False)
        elif algorithm_name == "dijkstra":
            if "graph" not in params:
                if not NX_AVAILABLE:
                    return False
                params["graph"] = nx.complete_graph(5)
                # 为边设置随机权重
                for u, v in params["graph"].edges():
                    params["graph"][u][v]["weight"] = random.randint(1, 10)
            else:
                # 确保 reset 时如果已存在图，不再重新分配随机权重
                graph = params["graph"]
                for u, v in graph.edges():
                    if "weight" not in graph[u][v]:
                        graph[u][v]["weight"] = random.randint(1, 10)
        elif algorithm_name == "convex_hull":
            if "points" not in params:
                params["points"] = [(random.randint(0, 100), random.randint(0, 100)) for _ in range(12)]
        elif algorithm_name == "kmeans":
            if "points" not in params:
                params["points"] = [(random.randint(0, 100), random.randint(0, 100)) for _ in range(15)]

        self.params = params

        algorithms = {
            "bubble_sort": self.bubble_sort_generator,
            "quick_sort": self.quick_sort_generator,
            "binary_search": self.binary_search_generator,
            "dijkstra": self.dijkstra_generator,
            "bfs": self.bfs_generator,
            "dfs": self.dfs_generator,
            "convex_hull": self.convex_hull_generator,
            "kmeans": self.kmeans_generator,
        }

        if algorithm_name in algorithms:
            self.generator = algorithms[algorithm_name](**params)
            self.current_state = None
            return True
        return False

    def step(self):
        if self.generator is None:
            return None
        try:
            self.current_state = next(self.generator)
            return self.current_state
        except StopIteration:
            self.current_state = None
            return None

    def reset(self):
        if self.current_algorithm and self.params:
            self.load_algorithm(self.current_algorithm, **self.params)
            self.current_state = None

    def get_state(self):
        return self.current_state

    def bubble_sort_generator(self, arr=None):
        if arr is None:
            arr = [random.randint(1, 100) for _ in range(8)]
        arr = arr.copy()
        n = len(arr)

        yield {
            "type": "sorting",
            "array": arr.copy(),
            "comparing": [],
            "swapping": [],
            "sorted": [],
            "description": t("algo_vis.desc.bubble.initial"),
        }

        for i in range(n):
            swapped = False
            for j in range(0, n - i - 1):
                yield {
                    "type": "sorting",
                    "array": arr.copy(),
                    "comparing": [j, j + 1],
                    "swapping": [],
                    "sorted": list(range(n - i, n)),
                    "description": t("algo_vis.desc.bubble.comparing", arr[j], arr[j + 1]),
                }

                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    swapped = True
                    yield {
                        "type": "sorting",
                        "array": arr.copy(),
                        "comparing": [],
                        "swapping": [j, j + 1],
                        "sorted": list(range(n - i, n)),
                        "description": t("algo_vis.desc.bubble.swapped", arr[j + 1], arr[j]),
                    }

            if not swapped:
                break

            yield {
                "type": "sorting",
                "array": arr.copy(),
                "comparing": [],
                "swapping": [],
                "sorted": list(range(n - i - 1, n)),
                "description": t("algo_vis.desc.bubble.pass_complete", i + 1),
            }

        yield {
            "type": "sorting",
            "array": arr.copy(),
            "comparing": [],
            "swapping": [],
            "sorted": list(range(n)),
            "description": t("algo_vis.desc.bubble.complete"),
        }

    def quick_sort_generator(self, arr=None):
        if arr is None:
            arr = [random.randint(1, 100) for _ in range(8)]
        arr = arr.copy()

        yield {
            "type": "sorting",
            "array": arr.copy(),
            "comparing": [],
            "swapping": [],
            "sorted": [],
            "pivot": -1,
            "description": t("algo_vis.desc.quick.initial"),
        }

        def quick_sort_helper(low, high):
            if low < high:
                pivot = arr[high]
                i = low - 1

                yield {
                    "type": "sorting",
                    "array": arr.copy(),
                    "comparing": [],
                    "swapping": [],
                    "sorted": [],
                    "pivot": high,
                    "partition": (low, high),
                    "description": t("algo_vis.desc.quick.pivot", pivot),
                }

                for j in range(low, high):
                    yield {
                        "type": "sorting",
                        "array": arr.copy(),
                        "comparing": [j, high],
                        "swapping": [],
                        "sorted": [],
                        "pivot": high,
                        "partition": (low, high),
                        "description": t("algo_vis.desc.quick.comparing_pivot", arr[j], pivot),
                    }

                    if arr[j] <= pivot:
                        i = i + 1
                        if i != j:
                            arr[i], arr[j] = arr[j], arr[i]
                            yield {
                                "type": "sorting",
                                "array": arr.copy(),
                                "comparing": [],
                                "swapping": [i, j],
                                "sorted": [],
                                "pivot": high,
                                "partition": (low, high),
                                "description": t("algo_vis.desc.quick.swapped", arr[j], arr[i]),
                            }

                arr[i + 1], arr[high] = arr[high], arr[i + 1]
                pi = i + 1

                yield {
                    "type": "sorting",
                    "array": arr.copy(),
                    "comparing": [],
                    "swapping": [pi, high],
                    "sorted": [pi],
                    "pivot": -1,
                    "description": t("algo_vis.desc.quick.pivot_placed", pivot, pi),
                }

                yield from quick_sort_helper(low, pi - 1)
                yield from quick_sort_helper(pi + 1, high)

        yield from quick_sort_helper(0, len(arr) - 1)

        yield {
            "type": "sorting",
            "array": arr.copy(),
            "comparing": [],
            "swapping": [],
            "sorted": list(range(len(arr))),
            "pivot": -1,
            "description": t("algo_vis.desc.quick.complete"),
        }

    def binary_search_generator(self, arr=None, target=None):
        if arr is None:
            arr = sorted([random.randint(1, 100) for _ in range(10)])
        if target is None:
            target = arr[random.randint(0, len(arr) - 1)]

        low = 0
        high = len(arr) - 1

        yield {
            "type": "search",
            "array": arr.copy(),
            "target": target,
            "search_range": (low, high),
            "found": False,
            "description": t("algo_vis.desc.binary.searching", target),
        }

        while low <= high:
            mid = (low + high) // 2

            yield {
                "type": "search",
                "array": arr.copy(),
                "target": target,
                "search_range": (low, high),
                "mid": mid,
                "found": False,
                "description": t("algo_vis.desc.binary.check_mid", mid, arr[mid]),
            }

            if arr[mid] == target:
                yield {
                    "type": "search",
                    "array": arr.copy(),
                    "target": target,
                    "search_range": (mid, mid),
                    "mid": mid,
                    "found": True,
                    "description": t("algo_vis.desc.binary.found", target, mid),
                }
                return
            elif arr[mid] < target:
                low = mid + 1
                yield {
                    "type": "search",
                    "array": arr.copy(),
                    "target": target,
                    "search_range": (low, high),
                    "mid": mid,
                    "found": False,
                    "description": t("algo_vis.desc.binary.go_right", arr[mid], target),
                }
            else:
                high = mid - 1
                yield {
                    "type": "search",
                    "array": arr.copy(),
                    "target": target,
                    "search_range": (low, high),
                    "mid": mid,
                    "found": False,
                    "description": t("algo_vis.desc.binary.go_left", arr[mid], target),
                }

        yield {
            "type": "search",
            "array": arr.copy(),
            "target": target,
            "search_range": (-1, -1),
            "found": False,
            "description": t("algo_vis.desc.binary.not_found", target),
        }

    def bfs_generator(self, graph=None, start=0):
        # [P0修复 Bug2] 进入函数先检查依赖
        if not NX_AVAILABLE:
            yield {"type": "error", "description": t("algo_vis.desc.error.nx_missing")}
            return
        if graph is None:
            graph = nx.erdos_renyi_graph(6, 0.5, directed=False)

        # 预计算：避免每步 yield 都重复 list() 转换
        _nodes = list(graph.nodes())
        _edges = list(graph.edges())
        adj_list = {n: list(graph.neighbors(n)) for n in graph.nodes()}
        visited = {n: False for n in graph.nodes()}
        queue = deque([start])
        visited[start] = True
        order = []

        yield {
            "type": "graph",
            "nodes": _nodes,
            "edges": _edges,
            "visited": visited.copy(),
            "current": start,
            "queue": list(queue),
            "order": order.copy(),
            "description": t("algo_vis.desc.bfs.start", start),
        }

        while queue:
            node = queue.popleft()
            order.append(node)

            yield {
                "type": "graph",
                "nodes": _nodes,
                "edges": _edges,
                "visited": visited.copy(),
                "current": node,
                "queue": queue.copy(),
                "order": order.copy(),
                "description": t("algo_vis.desc.bfs.processing", node),
            }

            for neighbor in adj_list[node]:
                if not visited[neighbor]:
                    visited[neighbor] = True
                    queue.append(neighbor)

                    yield {
                        "type": "graph",
                        "nodes": _nodes,
                        "edges": _edges,
                        "visited": visited.copy(),
                        "current": neighbor,
                        "queue": queue.copy(),
                        "order": order.copy(),
                        "description": t("algo_vis.desc.bfs.visit_neighbor", neighbor),
                    }

        yield {
            "type": "graph",
            "nodes": _nodes,
            "edges": _edges,
            "visited": visited.copy(),
            "current": -1,
            "queue": [],
            "order": order.copy(),
            "description": t("algo_vis.desc.bfs.complete", order),
        }

    def dfs_generator(self, graph=None, start=0):
        # [P0修复 Bug2] 进入函数先检查依赖
        if not NX_AVAILABLE:
            yield {"type": "error", "description": t("algo_vis.desc.error.nx_missing")}
            return
        if graph is None:
            graph = nx.erdos_renyi_graph(6, 0.5, directed=False)

        # 预计算：避免每步 yield 都重复 list() 转换
        _nodes = list(graph.nodes())
        _edges = list(graph.edges())
        adj_list = {n: list(graph.neighbors(n)) for n in graph.nodes()}
        visited = {n: False for n in graph.nodes()}
        stack = [start]
        order = []

        yield {
            "type": "graph",
            "nodes": _nodes,
            "edges": _edges,
            "visited": visited.copy(),
            "current": start,
            "stack": stack.copy(),
            "order": order.copy(),
            "description": t("algo_vis.desc.dfs.start", start),
        }

        while stack:
            node = stack.pop()

            if visited[node]:
                continue

            visited[node] = True
            order.append(node)

            yield {
                "type": "graph",
                "nodes": _nodes,
                "edges": _edges,
                "visited": visited.copy(),
                "current": node,
                "stack": stack.copy(),
                "order": order.copy(),
                "description": t("algo_vis.desc.dfs.visiting", node),
            }

            for neighbor in reversed(adj_list[node]):
                if not visited[neighbor]:
                    stack.append(neighbor)

                    yield {
                        "type": "graph",
                        "nodes": _nodes,
                        "edges": _edges,
                        "visited": visited.copy(),
                        "current": neighbor,
                        "stack": stack.copy(),
                        "order": order.copy(),
                        "description": t("algo_vis.desc.dfs.add_neighbor", neighbor),
                    }

        yield {
            "type": "graph",
            "nodes": _nodes,
            "edges": _edges,
            "visited": visited.copy(),
            "current": -1,
            "stack": [],
            "order": order.copy(),
            "description": t("algo_vis.desc.dfs.complete", order),
        }

    def dijkstra_generator(self, graph=None, start=0):
        # [P0修复 Bug2] 进入函数先检查依赖
        if not NX_AVAILABLE:
            yield {"type": "error", "description": t("algo_vis.desc.error.nx_missing")}
            return
        if graph is None:
            graph = nx.complete_graph(5)

        # 确保所有边有权重
        for u, v in graph.edges():
            if "weight" not in graph[u][v]:
                graph[u][v]["weight"] = random.randint(1, 10)

        # 预计算：避免每步 yield 都重复 list comprehension
        _nodes = list(graph.nodes())
        _edges = [(u, v, graph[u][v]["weight"]) for u, v in graph.edges()]
        adj_list = {
            n: [(neighbor, graph[n][neighbor]["weight"]) for neighbor in graph.neighbors(n)] for n in graph.nodes()
        }

        distances = {n: float("inf") for n in graph.nodes()}
        distances[start] = 0
        visited = {n: False for n in graph.nodes()}
        pq = [(0, start)]
        path = {}

        yield {
            "type": "shortest_path",
            "nodes": _nodes,
            "edges": _edges,
            "distances": distances.copy(),
            "visited": visited.copy(),
            "current": start,
            "description": t("algo_vis.desc.dijkstra.start", start),
        }

        while pq:
            dist_u, u = heapq.heappop(pq)

            if visited[u]:
                continue

            visited[u] = True

            yield {
                "type": "shortest_path",
                "nodes": _nodes,
                "edges": _edges,
                "distances": distances.copy(),
                "visited": visited.copy(),
                "current": u,
                "description": t("algo_vis.desc.dijkstra.processing", u, dist_u),
            }

            for v, weight in adj_list[u]:
                if distances[v] > distances[u] + weight:
                    distances[v] = distances[u] + weight
                    path[v] = u
                    heapq.heappush(pq, (distances[v], v))

                    yield {
                        "type": "shortest_path",
                        "nodes": _nodes,
                        "edges": _edges,
                        "distances": distances.copy(),
                        "visited": visited.copy(),
                        "current": v,
                        "description": t("algo_vis.desc.dijkstra.updated", v, distances[v]),
                    }

        yield {
            "type": "shortest_path",
            "nodes": _nodes,
            "edges": _edges,
            "distances": distances.copy(),
            "visited": visited.copy(),
            "current": -1,
            "description": t("algo_vis.desc.dijkstra.complete", distances),
        }

    def convex_hull_generator(self, points=None):
        if points is None:
            points = [(random.randint(0, 100), random.randint(0, 100)) for _ in range(12)]

        points = sorted(points)

        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        yield {
            "type": "convex_hull",
            "points": points.copy(),
            "hull": [],
            "current_edge": None,
            "description": t("algo_vis.desc.convex.initial"),
        }

        lower = []
        for p in points:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                removed = lower.pop()
                yield {
                    "type": "convex_hull",
                    "points": points.copy(),
                    "hull": lower.copy(),
                    "current_edge": (lower[-1] if lower else None, p),
                    "removed_point": removed,
                    "description": t("algo_vis.desc.convex.remove_lower", removed),
                }
            lower.append(p)
            yield {
                "type": "convex_hull",
                "points": points.copy(),
                "hull": lower.copy(),
                "current_edge": (lower[-2] if len(lower) > 1 else None, p),
                "description": t("algo_vis.desc.convex.add_lower", p),
            }

        upper = []
        for p in reversed(points):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                removed = upper.pop()
                yield {
                    "type": "convex_hull",
                    "points": points.copy(),
                    "hull": lower + upper,
                    "current_edge": (upper[-1] if upper else None, p),
                    "removed_point": removed,
                    "description": t("algo_vis.desc.convex.remove_upper", removed),
                }
            upper.append(p)
            yield {
                "type": "convex_hull",
                "points": points.copy(),
                "hull": lower + upper,
                "current_edge": (upper[-2] if len(upper) > 1 else None, p),
                "description": t("algo_vis.desc.convex.add_upper", p),
            }

        full_hull = lower[:-1] + upper[:-1]

        yield {
            "type": "convex_hull",
            "points": points.copy(),
            "hull": full_hull,
            "current_edge": None,
            "description": t("algo_vis.desc.convex.complete", full_hull),
        }

    def kmeans_generator(self, points=None, k=3):
        if points is None:
            points = [(random.randint(0, 100), random.randint(0, 100)) for _ in range(15)]

        if k > len(points):
            yield {
                "type": "error",
                "description": t("algo_vis.desc.error.kmeans_failed", len(points), k),
            }
            return

        centers = random.sample(points, k)
        clusters = [[] for _ in range(k)]

        yield {
            "type": "clustering",
            "points": points.copy(),
            "centers": centers.copy(),
            "clusters": clusters.copy(),
            "iteration": 0,
            "description": t("algo_vis.desc.kmeans.initial_centers", centers),
        }

        iteration = 0
        max_iterations = 10

        while iteration < max_iterations:
            clusters = [[] for _ in range(k)]

            for point in points:
                distances = [((point[0] - c[0]) ** 2 + (point[1] - c[1]) ** 2) ** 0.5 for c in centers]
                cluster_idx = distances.index(min(distances))
                clusters[cluster_idx].append(point)

                yield {
                    "type": "clustering",
                    "points": points.copy(),
                    "centers": centers.copy(),
                    "clusters": [list(c) for c in clusters],
                    "current_point": point,
                    "assigned_cluster": cluster_idx,
                    "iteration": iteration,
                    "description": t("algo_vis.desc.kmeans.assigning", point, cluster_idx),
                }

            new_centers = []
            for i, cluster in enumerate(clusters):
                if cluster:
                    new_center = (
                        sum(p[0] for p in cluster) / len(cluster),
                        sum(p[1] for p in cluster) / len(cluster),
                    )
                else:
                    new_center = centers[i]
                    new_centers.append(new_center)  # 先 append，再 yield，与非空分支一致
                    yield {
                        "type": "clustering",
                        "points": points.copy(),
                        "centers": new_centers + centers[i + 1 :],
                        "clusters": [list(c) for c in clusters],
                        "updated_center": i,
                        "iteration": iteration,
                        "description": t("algo_vis.desc.kmeans.empty_cluster", i, new_center),
                    }
                    continue
                new_centers.append(new_center)

                yield {
                    "type": "clustering",
                    "points": points.copy(),
                    "centers": new_centers + centers[i + 1 :],
                    "clusters": [list(c) for c in clusters],
                    "updated_center": i,
                    "iteration": iteration,
                    "description": t("algo_vis.desc.kmeans.updating_center", i, new_center),
                }

            max_distance = max(
                ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2) ** 0.5 for c1, c2 in zip(new_centers, centers)
            )
            if max_distance < 1e-6:
                break

            centers = new_centers
            iteration += 1

            yield {
                "type": "clustering",
                "points": points.copy(),
                "centers": centers.copy(),
                "clusters": [list(c) for c in clusters],
                "iteration": iteration,
                "description": t("algo_vis.desc.kmeans.iteration_complete", iteration),
            }

        yield {
            "type": "clustering",
            "points": points.copy(),
            "centers": centers.copy(),
            "clusters": [list(c) for c in clusters],
            "iteration": iteration,
            "description": t("algo_vis.desc.kmeans.complete", iteration),
        }
