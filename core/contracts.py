"""
EsnafDoktor (MerchantDoctor) - Core Type Contracts & Schemas
Hacktoberfest Elazığ 2026 - Week 2 "Side Hustle"

Strict TypedDict schemas ensuring zero data leakage, type safety, 
and seamless communication between BERTurk NLU, TabPFN Tabular Engine,
Advanced Hybrid RAG, and Local Gemma Inference.
"""
from __future__ import annotations

from typing import Literal, TypedDict

CategoryType = Literal["kargo", "iade", "urun", "teknik", "genel"]
IntentType = Literal["sikayet", "bilgi_talebi", "tesekkur"]
RiskLevel = Literal["green", "yellow", "red"]


class NLUResult(TypedDict):
    """Output from BERTurk sequence classification pipeline."""
    category: CategoryType
    category_confidence: float
    intent: IntentType
    intent_confidence: float
    sentiment_score: float  # -1.0 (pure complaint) to +1.0 (gratitude)
    latency_ms: float
    model_name: str


class RetrievedEvidence(TypedDict):
    """An individual policy snippet retrieved and scored by the Advanced RAG pipeline."""
    policy_id: str
    title: str
    category: str
    content: str
    bm25_rank: int
    dense_rank: int
    rrf_score: float
    reranker_score: float
    confidence_passed: bool


class RAGResult(TypedDict):
    """Combined output from Hybrid Retrieval (BM25 + Dense E5 + Cross-Encoder)."""
    query: str
    top_evidences: list[RetrievedEvidence]
    best_policy_id: str
    grounding_verified: bool
    retrieval_latency_ms: float
    rerank_latency_ms: float


class OrderFeatures(TypedDict):
    """Tabular order metadata used by TabPFN to detect dispute / fraud / churn risk."""
    order_id: str
    order_amount_tl: float
    delivery_days: int
    past_orders_count: int
    past_returns_count: int
    unboxing_video_available: bool
    box_damaged_reported: bool


class TabularRiskResult(TypedDict):
    """TabPFN dispute / abuse probability calibrated prediction."""
    risk_score: float  # 0.0 (safe) to 1.0 (high fraud / ungrounded dispute risk)
    risk_level: RiskLevel  # <0.30 green (Safe), 0.30-0.65 yellow (Review), >0.65 red (High Risk)
    risk_factors: list[str]
    method: Literal["tabpfn", "calibrated_rf_fallback"]
    latency_ms: float


class ActionCard(TypedDict):
    """Actionable merchant resolution card produced for the store owner."""
    suggested_action: str  # e.g., "Kargoya Hasar Tazmin Talebi Aç", "Şartsız İade Onayla"
    priority: Literal["dusuk", "orta", "yuksek", "acil"]
    grounded_rule: str
    merchant_instructions: list[str]
    customer_reply_tr: str
    reasoning_steps: list[str]
    voice_summary_tr: str
    offline_verified: bool
    total_cost_tl: float  # API cost: always 0.00 TL


class ComprehensiveDiagnosis(TypedDict):
    """End-to-end diagnosis object uniting all modular intelligence."""
    merchant_name: str
    customer_message: str
    nlu: NLUResult
    rag: RAGResult
    risk: TabularRiskResult
    action_card: ActionCard
    total_latency_ms: float
    timestamp: str
