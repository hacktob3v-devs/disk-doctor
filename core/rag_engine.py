"""
EsnafDoktor - 2026 Advanced Agentic RAG Engine
Hacktoberfest Elazığ 2026 - Week 2 "Side Hustle"

Architecture:
1. Lexical Retrieval: Turkish Okapi BM25 with token-level stemming/normalization.
2. Dense Semantic Retrieval: Local multilingual-e5-small embedding vectors (cosine similarity).
3. Hybrid Fusion: Reciprocal Rank Fusion (RRF, k=60).
4. Re-Ranking: Local Cross-Encoder semantic score calibration.
5. Self-RAG & Hallucination Guard: Validates token support and minimum relevance threshold.
"""
from __future__ import annotations

import json
import math
import os
import re
import time
from pathlib import Path
from typing import Any

import numpy as np

from core.contracts import RAGResult, RetrievedEvidence

# transformers 5.x loads weights on a thread pool, which intermittently segfaults
# on Windows when TabPFN/torch are imported in the same process. Load sequentially.
os.environ.setdefault("HF_DEACTIVATE_ASYNC_LOAD", "1")

RERANK_POOL = 16
CE_WEIGHT = 0.5

ROOT_DIR = Path(__file__).resolve().parents[1]
POLICIES_PATH = ROOT_DIR / "data" / "policies.json"
LOCAL_EMB_PATH = ROOT_DIR.parent / "disk-doctor" / "models" / "rag" / "embedding"
LOCAL_RERANK_PATH = ROOT_DIR.parent / "disk-doctor" / "models" / "rag" / "reranker"

TURKISH_STOPWORDS = {
    "ve", "veya", "ile", "icin", "icin", "gibi", "bir", "bu", "su", "o", "ne",
    "nasil", "nerede", "mi", "mu", "mu", "mi", "miyim", "miyiz", "hala", "cok",
    "daha", "ben", "bana", "benim", "sen", "sana", "biz", "bize", "de", "da",
    "ise", "ki", "ama", "fakat", "lakin", "ancak", "ya", "hem", "her", "hic"
}


def _normalize(text: str) -> str:
    charmap = str.maketrans({
        "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "I": "i",
        "İ": "i", "ö": "o", "Ö": "o", "ş": "s", "Ş": "s", "ü": "u", "Ü": "u"
    })
    return text.lower().translate(charmap)


def _tokenize(text: str) -> list[str]:
    norm = _normalize(text)
    words = re.findall(r"[a-z0-9]+", norm)
    return [w for w in words if len(w) > 2 and w not in TURKISH_STOPWORDS]


class BM25Retriever:
    """In-memory Okapi BM25 index over policy corpus."""
    def __init__(self, docs: list[dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.docs = docs
        self.corpus_size = len(docs)
        self.tokenized_docs = [_tokenize(d["title"] + " " + d["text"] + " " + " ".join(d.get("keywords", []))) for d in docs]
        self.doc_lens = [len(td) for td in self.tokenized_docs]
        self.avg_doc_len = sum(self.doc_lens) / max(1, self.corpus_size)

        # Inverted document frequency
        self.df: dict[str, int] = {}
        for td in self.tokenized_docs:
            for term in set(td):
                self.df[term] = self.df.get(term, 0) + 1

        self.idf: dict[str, float] = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def score(self, query: str) -> list[float]:
        q_tokens = _tokenize(query)
        scores = []
        for doc_tokens, doc_len in zip(self.tokenized_docs, self.doc_lens):
            score = 0.0
            doc_counts = {}
            for t in doc_tokens:
                doc_counts[t] = doc_counts.get(t, 0) + 1

            for qt in q_tokens:
                if qt in doc_counts:
                    tf = doc_counts[qt]
                    idf = self.idf.get(qt, 0.0)
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len))
                    score += idf * (numerator / denominator)
            scores.append(score)
        return scores


class DenseRetriever:
    """Semantic vector retriever using local sentence-transformers / E5."""
    def __init__(self, docs: list[dict[str, Any]]):
        self.docs = docs
        self.model = None
        self.doc_embeddings: np.ndarray | None = None
        self._init_model()

    def _init_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            model_path = str(LOCAL_EMB_PATH) if LOCAL_EMB_PATH.exists() else "intfloat/multilingual-e5-small"
            self.model = SentenceTransformer(model_path)
            passages = [f"passage: {d['title']} - {d['text']}" for d in self.docs]
            self.doc_embeddings = self.model.encode(passages, normalize_embeddings=True, show_progress_bar=False)
        except Exception as exc:
            print(f"[RAG Dense Info] Offline embedding model fallback active ({exc}).")
            self.model = None

    def score(self, query: str) -> list[float]:
        if self.model is None or self.doc_embeddings is None:
            # Calibrated keyword overlap vector fallback
            q_tokens = set(_tokenize(query))
            scores = []
            for d in self.docs:
                d_tokens = set(_tokenize(d["title"] + " " + d["text"]))
                jaccard = len(q_tokens & d_tokens) / max(1, len(q_tokens | d_tokens))
                scores.append(float(jaccard))
            return scores

        q_emb = self.model.encode([f"query: {query}"], normalize_embeddings=True)[0]
        cos_sim = np.dot(self.doc_embeddings, q_emb)
        return cos_sim.tolist()


class AdvancedRAGEngine:
    """Orchestrates Hybrid Retrieval (BM25 + Dense) + RRF + Cross-Encoder Rerank."""
    def __init__(self):
        with open(POLICIES_PATH, "r", encoding="utf-8") as f:
            self.policies = json.load(f)

        self.bm25 = BM25Retriever(self.policies)
        self.dense = DenseRetriever(self.policies)
        self.reranker_model = None
        self._init_reranker()

    def _init_reranker(self):
        try:
            from sentence_transformers import CrossEncoder
            if LOCAL_RERANK_PATH.exists():
                self.reranker_model = CrossEncoder(str(LOCAL_RERANK_PATH))
        except Exception:
            self.reranker_model = None

    def retrieve(self, query: str, top_k: int = 3) -> RAGResult:
        t0 = time.perf_counter()

        # 1. Lexical BM25 Ranking
        bm25_scores = self.bm25.score(query)
        bm25_ranked_indices = np.argsort(bm25_scores)[::-1]
        bm25_rank_dict = {idx: rank for rank, idx in enumerate(bm25_ranked_indices)}

        # 2. Dense Semantic Ranking
        dense_scores = self.dense.score(query)
        dense_ranked_indices = np.argsort(dense_scores)[::-1]
        dense_rank_dict = {idx: rank for rank, idx in enumerate(dense_ranked_indices)}

        t_retrieval = (time.perf_counter() - t0) * 1000

        # 3. Reciprocal Rank Fusion (k=60)
        k_rrf = 60
        fused_candidates: list[dict[str, Any]] = []
        for idx in range(len(self.policies)):
            r_bm25 = bm25_rank_dict[idx]
            r_dense = dense_rank_dict[idx]
            rrf_score = (1.0 / (k_rrf + r_bm25)) + (1.0 / (k_rrf + r_dense))
            fused_candidates.append({
                "idx": idx,
                "policy": self.policies[idx],
                "bm25_rank": r_bm25 + 1,
                "dense_rank": r_dense + 1,
                "rrf_score": rrf_score,
                "bm25_score": bm25_scores[idx],
                "dense_score": dense_scores[idx]
            })

        fused_candidates.sort(key=lambda x: x["rrf_score"], reverse=True)
        # The policy corpus is small, so every policy is re-ranked
        top_candidates = fused_candidates[:max(RERANK_POOL, top_k)]

        # 4. Re-Ranking: fused lexical/semantic score + policy keyword bonus,
        #    nudged by the multilingual Cross-Encoder. The Cross-Encoder alone is too
        #    flat on short Turkish policies to decide (17/21 vs 20/21 policy Hit@1 on
        #    the colloquial set in scripts/evaluate_rag_policy.py), so it only re-weights.
        t_rerank_start = time.perf_counter()
        q_norm = _normalize(query)
        for c in top_candidates:
            kw_bonus = sum(2.0 for kw in c["policy"].get("keywords", []) if kw in q_norm)
            c["rerank_score"] = c["rrf_score"] * 10.0 + kw_bonus + (c["dense_score"] * 2.0)
        if self.reranker_model is not None:
            pairs = [[query, f"{c['policy']['title']}: {c['policy']['text']}"] for c in top_candidates]
            ce_scores = np.asarray(self.reranker_model.predict(pairs), dtype=float)
            ce_z = (ce_scores - ce_scores.mean()) / (ce_scores.std() + 1e-6)
            for c, z in zip(top_candidates, ce_z):
                c["rerank_score"] += CE_WEIGHT * float(z)
        top_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        t_rerank = (time.perf_counter() - t_rerank_start) * 1000

        # 5. Build Evidences & Self-RAG Grounding Verification
        evidences: list[RetrievedEvidence] = []
        q_tokens = set(_tokenize(query))

        for c in top_candidates[:top_k]:
            pol = c["policy"]
            pol_tokens = set(_tokenize(pol["title"] + " " + pol["text"]))
            overlap = len(q_tokens & pol_tokens)
            # Grounding is verified if there's solid lexical overlap or top dense rank
            has_confidence = overlap >= 1 or c["dense_rank"] == 1 or c["rrf_score"] > 0.025

            evidences.append({
                "policy_id": pol["id"],
                "title": pol["title"],
                "category": pol["category"],
                "content": pol["text"],
                "bm25_rank": c["bm25_rank"],
                "dense_rank": c["dense_rank"],
                "rrf_score": round(float(c["rrf_score"]), 5),
                "reranker_score": round(float(c["rerank_score"]), 4),
                "confidence_passed": has_confidence,
            })

        best_pol_id = evidences[0]["policy_id"] if evidences else "POL_GENEL_01"
        is_grounded = evidences[0]["confidence_passed"] if evidences else False

        return {
            "query": query,
            "top_evidences": evidences,
            "best_policy_id": best_pol_id,
            "grounding_verified": is_grounded,
            "retrieval_latency_ms": round(t_retrieval, 2),
            "rerank_latency_ms": round(t_rerank, 2),
        }


_global_engine: AdvancedRAGEngine | None = None


def get_rag_engine() -> AdvancedRAGEngine:
    global _global_engine
    if _global_engine is None:
        _global_engine = AdvancedRAGEngine()
    return _global_engine


def retrieve_policies(query: str, top_k: int = 3) -> RAGResult:
    engine = get_rag_engine()
    return engine.retrieve(query, top_k=top_k)
