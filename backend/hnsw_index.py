import random
import math
from typing import List, Dict, Any
from vector_utils import Vector, dot, l2_distance, normalize


class _BinaryHeap:
    """
    Minimal manual binary heap (priority queue).

    Stores items and orders them by `key(item)`. If `reverse=True`, the heap becomes
    a max-heap (largest key at the top); otherwise a min-heap.
    """

    def __init__(self, *, key, reverse: bool = False):
        self._a: List[Any] = []
        self._key = key
        self._reverse = reverse

    def __len__(self) -> int:
        return len(self._a)

    def peek(self):
        return self._a[0]

    def push(self, item) -> None:
        a = self._a
        a.append(item)
        self._sift_up(len(a) - 1)

    def pop(self):
        a = self._a
        if not a:
            raise IndexError("pop from empty heap")
        last = a.pop()
        if not a:
            return last
        top = a[0]
        a[0] = last
        self._sift_down(0)
        return top

    def _better(self, i: int, j: int) -> bool:
        """Return True if a[i] should be above a[j]."""
        ki = self._key(self._a[i])
        kj = self._key(self._a[j])
        return ki > kj if self._reverse else ki < kj

    def _sift_up(self, idx: int) -> None:
        a = self._a
        while idx > 0:
            parent = (idx - 1) // 2
            if self._better(idx, parent):
                a[idx], a[parent] = a[parent], a[idx]
                idx = parent
            else:
                break

    def _sift_down(self, idx: int) -> None:
        a = self._a
        n = len(a)
        while True:
            left = 2 * idx + 1
            if left >= n:
                break
            right = left + 1
            best = left
            if right < n and self._better(right, left):
                best = right
            if self._better(best, idx):
                a[idx], a[best] = a[best], a[idx]
                idx = best
            else:
                break

class HNSWIndex:
    def __init__(self, M: int = 16, efConstruction: int = 100, efSearch: int = 50):
        self.M = M
        self.M0 = 2 * M # Max connections for layer 0
        self.efConstruction = efConstruction
        self.efSearch = efSearch
        
        self.m_L = 1 / math.log(M)
        self.vectors: Dict[int, Vector] = {}
        self.metadata: Dict[int, Any] = {}
        
        # Multilayer graph structure
        self.graphs: Dict[int, Dict[int, List[int]]] = {} 
        self.enter_node = None
        self.max_layer = -1
        self.next_node_id = 0

    def _normalize(self, v: Any) -> Vector:
        return normalize(v)

    def l2_distance(self, v1: Vector, v2: Vector) -> float:
        return l2_distance(v1, v2)

    def cosine_similarity(self, v1: Vector, v2: Vector) -> float:
        # Vectors are normalized on insert/search, so dot is cosine similarity.
        return float(dot(v1, v2))

    def _get_random_layer(self) -> int:
        return math.floor(-math.log(random.uniform(1e-6, 1.0)) * self.m_L)

    def search_layer(self, query: Vector, entry_points: List[int], ef: int, layer: int) -> List[int]:
        """Greedy search algorithm on a specific layer."""
        candidates = _BinaryHeap(key=lambda x: x[0], reverse=False)  # (dist, node) min-heap
        nearest_neighbors = _BinaryHeap(key=lambda x: x[0], reverse=True)  # (dist, node) max-heap by dist
        visited = set(entry_points)
        
        for ep in entry_points:
            dist = self.l2_distance(query, self.vectors[ep])
            candidates.push((dist, ep))
            nearest_neighbors.push((dist, ep))
            
        while len(candidates) > 0:
            c_dist, c = candidates.pop()
            if len(nearest_neighbors) == 0:
                break
            f_dist, _ = nearest_neighbors.peek()
            
            if c_dist > f_dist:
                break
                
            for neighbor in self.graphs[layer].get(c, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    n_dist = self.l2_distance(query, self.vectors[neighbor])
                    f_dist_top, _ = nearest_neighbors.peek()
                    
                    if n_dist < f_dist_top or len(nearest_neighbors) < ef:
                        candidates.push((n_dist, neighbor))
                        nearest_neighbors.push((n_dist, neighbor))
                        
                        if len(nearest_neighbors) > ef:
                            nearest_neighbors.pop()
                            
        res = []
        while len(nearest_neighbors) > 0:
            d, n = nearest_neighbors.pop()
            res.append(n)
        return res[::-1]

    def _select_neighbors(self, query: Vector, candidates: List[int], M: int, layer: int) -> List[int]:
        """Neighbor selection heuristic."""
        candidates_sorted = sorted([(self.l2_distance(query, self.vectors[c]), c) for c in candidates])
        return [c for _, c in candidates_sorted[:M]]

    def insert(self, vector: Any, meta: Any = None) -> int:
        """Insertion of new vectors into the graph."""
        node_id = self.next_node_id
        self.next_node_id += 1

        vector = self._normalize(vector)
        self.vectors[node_id] = vector
        self.metadata[node_id] = meta or {}
        
        l = self._get_random_layer()
        
        for layer in range(max(self.max_layer, l) + 1):
            if layer not in self.graphs:
                self.graphs[layer] = {}
            if node_id not in self.graphs[layer] and layer <= l:
                self.graphs[layer][node_id] = []

        if self.enter_node is None:
            self.enter_node = node_id
            self.max_layer = l
            return node_id
            
        curr_obj = self.enter_node
        
        for layer in range(self.max_layer, l, -1):
            nearest = self.search_layer(vector, [curr_obj], 1, layer)
            if nearest:
                curr_obj = nearest[0]
                
        entry_points = [curr_obj]
        for layer in range(min(self.max_layer, l), -1, -1):
            nearest = self.search_layer(vector, entry_points, self.efConstruction, layer)
            
            M_max = self.M0 if layer == 0 else self.M
            neighbors = self._select_neighbors(vector, nearest, self.M, layer)
            
            self.graphs[layer][node_id] = neighbors
            for n in neighbors:
                self.graphs[layer][n].append(node_id)
                
                if len(self.graphs[layer][n]) > M_max:
                    n_neighbors = self.graphs[layer][n]
                    pruned = self._select_neighbors(self.vectors[n], n_neighbors, M_max, layer)
                    self.graphs[layer][n] = pruned
                    
            entry_points = nearest

        if l > self.max_layer:
            self.max_layer = l
            self.enter_node = node_id
            
        return node_id

    def search(self, query_vector: Any, k: int = 5) -> List[Dict]:
        """Search the graph for nearest neighbors to the query vector."""
        if self.enter_node is None:
            return []

        query_vector = self._normalize(query_vector)
        curr_obj = self.enter_node
        for layer in range(self.max_layer, 0, -1):
            nearest = self.search_layer(query_vector, [curr_obj], 1, layer)
            if nearest:
                curr_obj = nearest[0]
                
        nearest = self.search_layer(query_vector, [curr_obj], self.efSearch, 0)
        
        # Sort by distance (on normalized vectors, L2 distance is monotonic w.r.t cosine similarity)
        nearest_sorted = sorted([(self.l2_distance(query_vector, self.vectors[n]), n) for n in nearest])
        
        results = []
        for dist, n in nearest_sorted[:k]:
            similarity = self.cosine_similarity(query_vector, self.vectors[n])
            cosine_distance = 1.0 - similarity
            results.append({
                "id": n,
                "text": self.metadata[n].get("text", "Unknown Document"),
                "similarity": float(similarity),
                "distance": float(dist),
                "cosine_distance": float(cosine_distance),
                "vector": self.vectors[n] # needed for frontend visualization
            })
            
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results

    def get_stats(self) -> Dict:
        """Returns statistics about the HNSW index."""
        vectors_count = len(self.vectors)
        layers = self.max_layer + 1
        
        edges_count = 0
        nodes_count = 0
        graph_structure = []
        
        for l in range(layers):
            layer_nodes = []
            layer_edges = []
            for node, neighbors in self.graphs.get(l, {}).items():
                layer_nodes.append(node)
                edges_count += len(neighbors)
                nodes_count += 1
                for neighbor in neighbors:
                    layer_edges.append([node, neighbor])
            
            graph_structure.append({
                "layer": l,
                "nodes": layer_nodes,
                "edges": layer_edges
            })
                
        avg_conn = edges_count / nodes_count if nodes_count > 0 else 0
        
        return {
            "total_vectors": vectors_count,
            "graph_layers": layers,
            "average_connections": round(avg_conn, 2),
            "graph_structure": graph_structure
        }
