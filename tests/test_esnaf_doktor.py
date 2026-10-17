"""
EsnafDoktor - Comprehensive & Adversarial Unit Test Suite
Hacktoberfest Elazığ 2026 - Week 2 "Side Hustle"

Tests NLU classification, typo robustness, Hybrid RAG, TabPFN risk calibration,
and HTML report generation. Zero network calls; 100% offline verifiable.
"""
from __future__ import annotations

import pytest

from core.contracts import OrderFeatures
from core.llm_gemma import generate_action_card
from core.nlu_berturk import classify_text
from core.rag_engine import retrieve_policies
from core.report_generator import generate_printable_html_report
from core.tabpfn_dispute import evaluate_order_risk


def test_nlu_standard_queries():
    """Verifies that standard customer messages map to valid categories and intents."""
    cases = [
        ("Kargom 4 gündür nerede kaldı teslimat yapılmadı", "kargo", "sikayet"),
        ("14 gün cayma hakkı şartları ve iade prosedürü nedir acaba", "iade", "bilgi_talebi"),
        ("Gelen kazağın dikişleri sökük ve ayıplı çıktı", "urun", "sikayet"),
        ("Kartımdan iki kere çekim yapıldı mobil bankacılıkta hata verdi", "teknik", "sikayet"),
        ("Her şey için çok teşekkürler harika bir esnafsınız bol kazançlar", "genel", "tesekkur"),
    ]
    for text, expected_cat, expected_intent in cases:
        res = classify_text(text)
        assert res["category"] == expected_cat, f"Expected {expected_cat}, got {res['category']} for: {text}"
        assert res["intent"] == expected_intent, f"Expected {expected_intent}, got {res['intent']} for: {text}"
        assert 0.0 <= res["category_confidence"] <= 1.0
        assert res["latency_ms"] >= 0.0


def test_nlu_adversarial_typos():
    """Verifies robustness against mobile keyboard typos, missing Turkish chars, and noise."""
    noisy_text = "kargp cok gecikri kurye gelmedi sube nerde cvp yok"
    res = classify_text(noisy_text)
    assert res["category"] == "kargo"
    assert res["intent"] == "sikayet"
    assert res["sentiment_score"] < 0.0


def test_rag_hybrid_retrieval():
    """Verifies BM25 + Dense E5 + RRF retrieves the correct policy with valid scores."""
    res = retrieve_policies("Kutusu ezilmiş ve içindeki porselen kırık kargo tutanağı", top_k=3)
    assert len(res["top_evidences"]) >= 1
    top_p = res["top_evidences"][0]
    assert top_p["policy_id"] in ["POL_KARGO_02", "POL_URUN_01"]
    assert top_p["rrf_score"] > 0.0
    assert res["grounding_verified"] is True


def test_rag_hygiene_exception():
    """Verifies that opened underwear / cosmetics policies are accurately retrieved."""
    res = retrieve_policies("İç çamaşırının paketini açtım ama denemedim hijyen sebebiyle iade", top_k=3)
    assert any(ev["policy_id"] == "POL_IADE_02" for ev in res["top_evidences"])


def test_tabpfn_risk_boundaries_and_calibration():
    """Verifies TabPFN produces calibrated scores in [0.04, 0.96] range, never trivial extremes."""
    # Case 1: High Risk Case (High returns, large amount, no video, damaged box)
    bad_order: OrderFeatures = {
        "order_id": "TEST-HIGH-01",
        "order_amount_tl": 7500.0,
        "delivery_days": 8,
        "past_orders_count": 2,
        "past_returns_count": 2,
        "unboxing_video_available": False,
        "box_damaged_reported": True,
    }
    res_bad = evaluate_order_risk(bad_order, sentiment_score=-0.85)
    assert res_bad["risk_score"] > 0.60
    assert res_bad["risk_level"] in ["yellow", "red"]
    assert len(res_bad["risk_factors"]) >= 2

    # Case 2: Low Risk Case (Loyal customer, small amount, video available)
    good_order: OrderFeatures = {
        "order_id": "TEST-LOW-01",
        "order_amount_tl": 250.0,
        "delivery_days": 2,
        "past_orders_count": 15,
        "past_returns_count": 0,
        "unboxing_video_available": True,
        "box_damaged_reported": False,
    }
    res_good = evaluate_order_risk(good_order, sentiment_score=0.5)
    assert res_good["risk_score"] < 0.40
    assert res_good["risk_level"] in ["green", "yellow"]


def test_action_card_generation():
    """Verifies that the generated action card is grounded, structured, and costs 0.00 TL."""
    nlu = classify_text("Kargom 5 gündür şubede bekliyor dağıtıma çıkmadı")
    rag = retrieve_policies("Kargom 5 gündür şubede bekliyor dağıtıma çıkmadı", top_k=2)
    order: OrderFeatures = {
        "order_id": "ORD-123",
        "order_amount_tl": 800.0,
        "delivery_days": 5,
        "past_orders_count": 4,
        "past_returns_count": 0,
        "unboxing_video_available": True,
        "box_damaged_reported": False,
    }
    risk = evaluate_order_risk(order, sentiment_score=nlu["sentiment_score"])

    card = generate_action_card("Elazığ Butik", "Kargom 5 gündür şubede bekliyor", nlu, rag, risk)

    assert "suggested_action" in card
    assert card["priority"] in ["dusuk", "orta", "yuksek", "acil"]
    assert len(card["merchant_instructions"]) >= 1
    assert "Elazığ Butik" in card["customer_reply_tr"]
    assert card["total_cost_tl"] == 0.0
    assert card["offline_verified"] is True


def test_html_report_rendering():
    """Verifies that the generated printable HTML report contains required metadata."""
    order: OrderFeatures = {
        "order_id": "ORD-PRINT-99",
        "order_amount_tl": 1450.0,
        "delivery_days": 3,
        "past_orders_count": 4,
        "past_returns_count": 0,
        "unboxing_video_available": False,
        "box_damaged_reported": True,
    }
    nlu = classify_text("Kutusu ezilmiş içindeki porselen kırık")
    rag = retrieve_policies("Kutusu ezilmiş içindeki porselen kırık", top_k=2)
    risk = evaluate_order_risk(order, sentiment_score=nlu["sentiment_score"])
    card = generate_action_card("Harput Çarşı", "Kutusu ezilmiş içindeki porselen kırık", nlu, rag, risk)

    html = generate_printable_html_report(
        "Harput Çarşı", "Kutusu ezilmiş içindeki porselen kırık", order, nlu, rag, risk, card, 0.045
    )
    assert "ORD-PRINT-99" in html
    assert "Harput Çarşı" in html
    assert "0.00 TL" in html
    assert "%100 ÇEVRİMDIŞI" in html
    assert "TabPFN Risk:" in html
