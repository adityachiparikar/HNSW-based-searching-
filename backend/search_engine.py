from hnsw_index import HNSWIndex
from embedding_model import encode_text, get_embedding_info, get_embedding_mode
from dataset_loader import build_search_document
from typing import List, Dict, Any
import time
import re


FIELD_WEIGHTS = {
    "brand": 0.18,
    "brand name": 0.18,
    "company": 0.18,
    "company name": 0.18,
    "company names": 0.18,
    "make": 0.18,
    "manufacturer": 0.18,
    "model": 0.30,
    "car model": 0.30,
    "car name": 0.30,
    "car names": 0.30,
    "cars name": 0.30,
    "cars names": 0.30,
    "name": 0.30,
    "vehicle model": 0.30,
    "engine": 0.35,
    "engines": 0.35,
    "engine name": 0.35,
    "engine names": 0.35,
    "engine_type": 0.35,
    "engine type": 0.35,
    "motor": 0.35,
    "category": 0.14,
    "body": 0.12,
}


def _normalize_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()


def _tokens(value: Any) -> List[str]:
    return [token for token in _normalize_text(value).split() if token]


def _field_weight(key: str) -> float:
    return FIELD_WEIGHTS.get(_normalize_text(key), 0.08)


def _meaningful_phrase(value: str) -> bool:
    if len(value) >= 3:
        return True
    return len(value) >= 2 and any(char.isalpha() for char in value)

class SearchEngine:
    def __init__(self):
        self.index = HNSWIndex(M=16, efConstruction=100, efSearch=50)
        self.history = []
        self.documents: List[Dict[str, Any]] = []
        self._seen_texts = set()

    def reset(self):
        self.index = HNSWIndex(M=16, efConstruction=100, efSearch=50)
        self.documents = []
        self._seen_texts = set()

    def set_index_parameters(self, M: int, efConstruction: int, efSearch: int):
        self.index.M = M
        self.index.M0 = 2 * M
        self.index.efConstruction = efConstruction
        self.index.efSearch = efSearch

    def insert(self, items: List[Any]):
        if not items:
            return 0

        unique_docs = []
        for item in items:
            doc = build_search_document(item)
            key = doc["searchable_text"].casefold()
            if key not in self._seen_texts:
                unique_docs.append(doc)
                self._seen_texts.add(key)

        if not unique_docs:
            return 0

        embeddings = encode_text([doc["searchable_text"] for doc in unique_docs])
        count = 0
        for i, emb in enumerate(embeddings):
            doc = unique_docs[i]
            node_id = self.index.insert(emb, meta=doc)
            stored_doc = {
                "id": node_id,
                "text": doc["text"],
                "searchable_text": doc["searchable_text"],
                "fields": doc.get("fields", {}),
                "vector": self.index.vectors[node_id],
            }
            self.documents.append(stored_doc)
            count += 1
        return count

    def replace(self, items: List[Any]):
        self.reset()
        return self.insert(items)

    def _exact_boost(self, query: str, doc: Dict[str, Any]) -> Dict[str, Any]:
        query_norm = _normalize_text(query)
        query_tokens = set(_tokens(query))
        searchable_norm = _normalize_text(doc.get("searchable_text", ""))

        boost = 0.0
        reasons = []

        for key, value in doc.get("fields", {}).items():
            field_norm = _normalize_text(value)
            if not field_norm:
                continue

            field_tokens = set(field_norm.split())
            weight = _field_weight(key)
            exact_phrase = (
                query_norm == field_norm
                or (_meaningful_phrase(query_norm) and query_norm in field_norm)
                or (_meaningful_phrase(field_norm) and field_norm in query_norm)
            )
            token_overlap = len(query_tokens & field_tokens)

            if exact_phrase:
                boost += weight
                reasons.append(f"{key} exact match")
            elif token_overlap:
                boost += min(weight * 0.75, 0.06 * token_overlap)
                reasons.append(f"{key} token match")

        if query_norm and query_norm in searchable_norm:
            boost += 0.08
            reasons.append("row text contains query")

        return {"boost": min(boost, 0.55), "reasons": reasons}

    def _semantic_score(self, query_vector, doc_id: int) -> float:
        query_vector = self.index._normalize(query_vector)
        return self.index.cosine_similarity(query_vector, self.index.vectors[doc_id])

    def _format_result(self, doc: Dict[str, Any], semantic_score: float, exact_boost: float, reasons: List[str]) -> Dict[str, Any]:
        hybrid_score = min(1.0, max(0.0, (0.75 * max(0.0, semantic_score)) + exact_boost))
        return {
            "id": doc["id"],
            "text": doc["text"],
            "fields": doc.get("fields", {}),
            "searchable_text": doc.get("searchable_text", doc["text"]),
            "similarity": float(hybrid_score),
            "semantic_similarity": float(semantic_score),
            "exact_boost": float(exact_boost),
            "distance": float(1.0 - hybrid_score),
            "cosine_distance": float(1.0 - semantic_score),
            "match_reasons": reasons,
            "search_mode": "hybrid",
            "vector": doc["vector"],
        }

    def search(self, query: str, k: int = 20) -> Dict[str, Any]:
        start_time = time.time()
        k = max(1, min(int(k or 20), 100))
        query_vector = encode_text(query)
        semantic_candidates = self.index.search(query_vector, max(k * 5, 50))
        candidate_ids = {candidate["id"] for candidate in semantic_candidates}
        exact_info_by_id = {}

        for doc in self.documents:
            exact_info = self._exact_boost(query, doc)
            exact_info_by_id[doc["id"]] = exact_info
            if exact_info["boost"] > 0:
                candidate_ids.add(doc["id"])

        results = []
        has_exact_matches = any(info["boost"] > 0 for info in exact_info_by_id.values())
        for doc_id in candidate_ids:
            doc = self.documents[doc_id]
            semantic_score = self._semantic_score(query_vector, doc_id)
            exact_info = exact_info_by_id.get(doc_id, {"boost": 0.0, "reasons": []})
            result = self._format_result(doc, semantic_score, exact_info["boost"], exact_info["reasons"])
            if has_exact_matches and result["exact_boost"] <= 0 and result["semantic_similarity"] < 0.28:
                continue
            if not has_exact_matches and result["semantic_similarity"] < 0.12:
                continue
            results.append(result)

        results.sort(key=lambda item: (item["similarity"], item["exact_boost"], item["semantic_similarity"]), reverse=True)
        results = results[:k]
        end_time = time.time()
        latency = (end_time - start_time) * 1000 # convert to ms
        
        self.history.append({
            "query": query,
            "timestamp": time.time(),
            "latency_ms": latency,
            "top_k": k
        })
        
        return {
            "results": results,
            "latency": latency,
            "query": query,
            "k": k,
            "search_mode": "hybrid"
        }

    def stats(self) -> Dict[str, Any]:
        stats = self.index.get_stats()
        stats["history_count"] = len(self.history)
        stats["embedding_mode"] = get_embedding_mode()
        stats["embedding_info"] = get_embedding_info()
        return stats

engine = SearchEngine()
