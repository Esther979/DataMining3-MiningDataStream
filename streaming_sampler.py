from collections import defaultdict
import random


class StreamingGraphSampler:
    def __init__(self, M: int):
        self.M = M                      # reservoir 大小
        self.t = 0                      # 已经处理的边数
        self.reservoir = set()          # 当前被保留的边集合：{(u, v), ...}
        self.adj = defaultdict(set)     # 邻接表：u -> set of neighbors

    def process_edge(self, u, v):
        # 忽略自环
        if u == v:
            return

        # 保证 (u, v) 和 (v, u) 是同一条边
        edge = (u, v) if u < v else (v, u)

        # 如果这条边已经在 reservoir 中，就return
        if edge in self.reservoir:
            return

        # 边计数 +1 （第 t 条边）
        self.t += 1

        # reservoir 还没满，直接加入
        if len(self.reservoir) < self.M:
            self._add_edge(edge)

        # reservoir 已经满了，按概率决定是否替换
        else:
            accept_prob = self.M / self.t  # 接受新边的概率
            if random.random() < accept_prob:
                # 随机删掉一条旧边
                self._remove_random_edge()
                # 加入新边
                self._add_edge(edge)
            else:
                # 不接受这条边，什么都不做
                pass

    

    def _add_edge(self, edge):
    #加
        u, v = edge
        self.reservoir.add(edge)
        self.adj[u].add(v)
        self.adj[v].add(u)

    def _remove_random_edge(self):
    #选一条边删掉
        edge = random.choice(tuple(self.reservoir))
        self._remove_edge(edge)

    def _remove_edge(self, edge):
    #删
        u, v = edge

        # 从 reservoir 删除
        if edge in self.reservoir:
            self.reservoir.remove(edge)

        # 从邻接表中删除这条边
        if v in self.adj[u]:
            self.adj[u].remove(v)
        if u in self.adj[v]:
            self.adj[v].remove(u)

        # 如果某个节点已经没有邻居，把这个 key 删掉
        if len(self.adj[u]) == 0:
            del self.adj[u]
        if len(self.adj[v]) == 0:
            del self.adj[v]

    

    def get_reservoir_edges(self):
        #返回当前 reservoir 中所有边

        return self.reservoir

    def get_neighbors(self, u):
    
        #返回节点 u 的邻居集合；如果 u 不在图中，则返回空 set。
    
        return self.adj.get(u, set())


