from collections import defaultdict
import random
import time

# Basic Sampler of pool
class StreamingGraphSampler:
    def __init__(self, M: int):
        self.M = M
        self.t = 0
        self.reservoir = set()
        self.adj = defaultdict(set)

    def process_edge(self, u, v):
        if u == v: return
        edge = (u, v) if u < v else (v, u)
        if edge in self.reservoir: return
        
        self.t += 1
        if len(self.reservoir) < self.M:
            self._add_edge(edge)
        else:
            if random.random() < self.M / self.t:
                self._remove_random_edge()
                self._add_edge(edge)

    def _add_edge(self, edge):
        u, v = edge
        self.reservoir.add(edge)
        self.adj[u].add(v)
        self.adj[v].add(u)

    def _remove_random_edge(self):
        edge = random.choice(tuple(self.reservoir))
        self._remove_edge(edge)

    def _remove_edge(self, edge):
        u, v = edge
        if edge in self.reservoir:
            self.reservoir.remove(edge)
        if v in self.adj[u]:
            self.adj[u].remove(v)
        if u in self.adj[v]:
            self.adj[v].remove(u)
        if not self.adj[u]: del self.adj[u]
        if not self.adj[v]: del self.adj[v]

    def get_neighbors(self, u):
        return self.adj.get(u, set())


# TRIÈST-BASE (通过继承解决 O(M) 拷贝问题)
class TriestBase(StreamingGraphSampler):
    def __init__(self, M: int):
        super().__init__(M)
        self.tau = 0
        self.tau_local = defaultdict(int)

    def _add_edge(self, edge):
        # Rewrite：在添加物理边之前/之后更新计数
        # Base 算法在边进入采样时更新
        u, v = edge
        common = self.get_neighbors(u) & self.get_neighbors(v)
        count = len(common)
        if count > 0:
            self.tau += count
            self.tau_local[u] += count
            self.tau_local[v] += count
            for c in common:
                self.tau_local[c] += 1
        super()._add_edge(edge)

    def _remove_edge(self, edge):
        # Rewrite：在移除边之前更新计数
        # Base 算法在边移除采样时更新
        u, v = edge
        if edge in self.reservoir:
            common = self.get_neighbors(u) & self.get_neighbors(v)
            count = len(common)
            if count > 0:
                self.tau -= count
                self.tau_local[u] -= count
                self.tau_local[v] -= count
                for c in common:
                    self.tau_local[c] -= 1
        super()._remove_edge(edge)

    def get_global_estimate(self):
        # 论文公式
        if self.t <= self.M:
            return float(self.tau)
        xi = (self.t * (self.t - 1) * (self.t - 2)) / (self.M * (self.M - 1) * (self.M - 2))
        return xi * self.tau


# TRIÈST-IMPR 
class TriestImpr(StreamingGraphSampler):
    def __init__(self, M: int):
        super().__init__(M)
        self.tau = 0.0
        self.tau_local = defaultdict(float)

    def process_edge(self, u, v):
        if u == v: return
        edge = (u, v) if u < v else (v, u)
        if edge in self.reservoir: return

        # Simulation time step t 
        # UpdateCounters is called before sampling is decided.
        current_t = self.t + 1 
        
        # 1. Unconditional update counter
        self._update_counters(edge, current_t)
        
        # 2. Carry out sampling logic
        super().process_edge(u, v)

    def _update_counters(self, edge, t):
        u, v = edge
        common = self.get_neighbors(u) & self.get_neighbors(v)
        if not common: return
        
        # Weight calculation
        weight = 1.0
        if t > self.M:
            weight = ((t - 1) * (t - 2)) / (self.M * (self.M - 1))
        
        count = len(common)
        inc = weight * count
        self.tau += inc
        for c in common:
            self.tau_local[c] += weight
        self.tau_local[u] += inc
        self.tau_local[v] += inc

    def _remove_edge(self, edge):
        # IMPR: Remove edges without reducing the counter
        # Physical remove only
        super()._remove_edge(edge)

    def get_global_estimate(self):
        return self.tau

# Test the performance
def load_graph(filename):
    """Load the list of sides"""
    edges = []
    with open(filename, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                u, v = int(parts[0]), int(parts[1])
                if u != v:
                    edges.append((u, v))
    return edges

def exact_triangle_count_safe(edges):
    """Calculate Ground Truth (real value)"""
    adj = defaultdict(set)
    # Build a complete graph
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    
    triangles = 0
    # Iterative method for calculating triangles: sum(common_neighbors) / 3
    unique_edges = set()
    for u, v in edges:
        if u > v: u, v = v, u
        unique_edges.add((u, v))
        
    for u, v in unique_edges:
        common = adj[u] & adj[v]
        triangles += len(common)
        
    return triangles // 3

def run_facebook_test():
    filename = 'HW3/facebook_combined.txt'
    print(f"Loading the dataset: {filename} ...")
    try:
        edges = load_graph(filename)
        print(f"Total edges: {len(edges)}")
    except FileNotFoundError:
        print(f"Error: The file {filename} cannot be found.")
        return

    print("Calculating Ground Truth ...")
    start_time = time.time()
    true_count = exact_triangle_count_safe(edges)
    print(f"Ground Truth (The number of real triangles): {true_count} (Time cost: {time.time() - start_time:.4f}s)")
    print("-" * 90)
    
    # 测试不同的内存大小 M
    m_values = [1000, 5000, 10000, 20000, 40000]
    
    print(f"{'Algorithm':<15} | {'M':<8} | {'Sample %':<10} | {'Estimate':<12} | {'MAPE (%)':<10} | {'Time (s)':<10}")
    print("-" * 90)
    
    for M in m_values:
        sample_percent = (M / len(edges)) * 100
        
        # --- 测试 BASE ---
        algo_base = TriestBase(M)
        t0 = time.time()
        for u, v in edges:
            algo_base.process_edge(u, v)
        t1 = time.time()
        est_base = algo_base.get_global_estimate()
        mape_base = abs(est_base - true_count) / true_count * 100 if true_count > 0 else 0
        print(f"{'TRIÈST-BASE':<15} | {M:<8} | {sample_percent:<9.1f}% | {int(est_base):<12} | {mape_base:<10.2f} | {t1-t0:<10.4f}")
        
        # --- 测试 IMPR ---
        algo_impr = TriestImpr(M)
        t0 = time.time()
        for u, v in edges:
            algo_impr.process_edge(u, v)
        t1 = time.time()
        est_impr = algo_impr.get_global_estimate()
        mape_impr = abs(est_impr - true_count) / true_count * 100 if true_count > 0 else 0
        print(f"{'TRIÈST-IMPR':<15} | {M:<8} | {sample_percent:<9.1f}% | {int(est_impr):<12} | {mape_impr:<10.2f} | {t1-t0:<10.4f}")

if __name__ == "__main__":
    run_facebook_test()