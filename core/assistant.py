"""
EsnafDoktor - Customer conversation assistant.

Glues NLU -> hybrid RAG -> tabular risk -> action card into the single shape the
web interface consumes, decides whether a message can be answered automatically
or must be handed to the merchant, and streams a grounded reply from the local
open-weight model (Ollama).
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from typing import Any, Iterator, Literal

from core.contracts import OrderFeatures
from core.llm_gemma import OLLAMA_HOST, generate_action_card
from core.nlu_berturk import classify_text
from core.rag_engine import retrieve_policies
from core.tabpfn_dispute import evaluate_order_risk

Mode = Literal["question", "review"]

DEFAULT_MODEL = os.getenv("ED_GEMMA_MODEL", "gemma3:1b")

# Policies whose resolution needs evidence or a judgement call from the merchant
HANDOFF_POLICIES = {"POL_KARGO_02", "POL_IADE_03", "POL_URUN_01"}
# Of those, the ones where the assistant may still ask the customer for evidence (photos);
# every other handoff gets a holding message - the model never refuses a claim itself.
EVIDENCE_POLICIES = {"POL_KARGO_02", "POL_URUN_01"}
DISPUTE_CATEGORIES = {"iade", "urun"}

SUPPORT_HOURS = "09:00-19:00"


def _level(score: float) -> str:
    if score < 0.30:
        return "green"
    if score < 0.65:
        return "yellow"
    return "red"


def _risk_drivers(factors: list[str]) -> list[dict[str, str]]:
    drivers = []
    for f in factors:
        safe = f.startswith("Belirgin bir risk unsuru")
        drivers.append({"label": f, "dir": "down" if safe else "up"})
    return drivers


def analyze_message(
    message: str,
    order: OrderFeatures,
    mode: Mode = "question",
    stars: int = 0,
    merchant: str = "Usta Deri",
    customer: str = "",
) -> dict[str, Any]:
    """Runs the local pipeline once and returns the interface's analysis shape."""
    nlu = classify_text(message)
    intent, sentiment = nlu["intent"], nlu["sentiment_score"]
    if mode == "review" and stars:
        if stars >= 4 and intent != "sikayet":
            intent, sentiment = "tesekkur", max(sentiment, 0.6)
        elif stars <= 2:
            intent, sentiment = "sikayet", min(sentiment, -0.6)
    nlu = {**nlu, "intent": intent, "sentiment_score": sentiment}

    rag = retrieve_policies(message, top_k=2)
    if intent == "tesekkur":
        policy_id = "POL_GENEL_02"
    else:
        policy_id = rag["best_policy_id"]
    policy_category = policy_id.split("_")[1].lower()  # POL_IADE_03 -> iade

    # Policy-level retrieval is more reliable than the keyword NLU fallback
    # (see scripts/evaluate_rag_policy.py), so the matched policy decides the category.
    category = nlu["category"]
    if intent != "tesekkur" and policy_category != "genel":
        category = policy_category

    risk = evaluate_order_risk(order, sentiment_score=sentiment)
    dispute = intent != "tesekkur" and (
        category in DISPUTE_CATEGORIES or policy_category in DISPUTE_CATEGORIES or policy_id == "POL_KARGO_02"
    )
    score = risk["risk_score"] if dispute else round(0.02 + risk["risk_score"] * 0.25, 4)

    card = generate_action_card(
        merchant, message, {**nlu, "category": category}, rag,
        {**risk, "risk_score": score, "risk_level": _level(score)},
    )

    level = _level(score)
    if level == "red" or sentiment <= -0.85:
        priority = "acil"
    elif level == "yellow" or intent == "sikayet":
        priority = "yuksek"
    elif intent == "bilgi_talebi":
        priority = "orta"
    else:
        priority = "dusuk"

    escalate = (
        policy_id in HANDOFF_POLICIES
        or level == "red"
        or sentiment <= -0.85
        or (mode == "review" and intent == "sikayet")
    )

    evidence = next((e for e in rag["top_evidences"] if e["policy_id"] == policy_id), None)
    policy_title = evidence["title"] if evidence else ""
    first_name = customer.split(" ")[0] if customer else ""

    # Evidence-type handoffs still get a grounded reply (e.g. "send photos");
    # every other handoff gets a short holding message and the merchant decides.
    holding_reply = None
    if escalate and policy_id not in EVIDENCE_POLICIES and mode != "review":
        greet = f"Merhaba {first_name}, " if first_name else "Merhaba, "
        holding_reply = (
            f"{greet}mesajınızı aldım ve mağaza sahibimize öncelikli olarak ilettim. "
            f"Destek saatlerimiz içinde ({SUPPORT_HOURS}) size buradan dönüş yapılacak. {merchant}"
        )

    return {
        "category": category,
        "intent": intent,
        "confidence": round(float(nlu["category_confidence"]), 2),
        "sentiment": round(float(sentiment), 2),
        "risk": {"score": score, "level": level, "drivers": _risk_drivers(risk["risk_factors"]), "method": risk["method"]},
        "priority": priority,
        "action": card["suggested_action"],
        "steps": card["merchant_instructions"],
        "policyId": policy_id,
        "policyTitle": policy_title,
        "policyText": evidence["content"] if evidence else "",
        "grounded": rag["grounding_verified"],
        "reply": card["customer_reply_tr"],
        "holdingReply": holding_reply,
        "escalate": escalate,
        "timings": {
            "nlu": round(nlu["latency_ms"]),
            "rag": round(rag["retrieval_latency_ms"] + rag["rerank_latency_ms"]),
            "risk": round(risk["latency_ms"]),
            "llm": 0,
        },
        "models": {"nlu": nlu["model_name"], "risk": risk["method"]},
    }


def reply_prompt(
    message: str,
    policy_title: str,
    policy_text: str,
    merchant: str,
    customer: str,
    mode: Mode,
    stars: int,
    audience: Literal["customer", "merchant_draft"] = "customer",
) -> tuple[str, str]:
    system = (
        f"Sen {merchant} adlı küçük bir e-ticaret mağazasının müşteri temsilcisisin. "
        "Yalnızca verilen mağaza kuralındaki bilgileri kullan. Kuralda yazmayan hiçbir süre, gün, tutar, "
        "ücret, kod, koşul veya söz ekleme; emin olmadığın konuda mağaza sahibinin dönüş yapacağını söyle. "
        "2-4 kısa cümlelik, sade, samimi ve saygılı bir Türkçe yaz. Emoji, madde işareti, başlık kullanma. "
        f"'Merhaba <müşterinin ilk adı>,' diye başla ve yanıtı yalnızca '{merchant}' imzasıyla bitir."
    )
    kind = f"{stars} yıldızlı ürün yorumu (herkese açık yanıt yaz)" if mode == "review" else "satıcıya soru"
    first_name = customer.split(" ")[0] if customer else ""
    user = (
        f"Müşterinin ilk adı: {first_name or 'bilinmiyor, yalnızca Merhaba diye başla'}\n"
        f"Mesaj türü: {kind}\n"
        f"Mesaj: {message}\n\n"
        f"Uygulanacak mağaza kuralı: {policy_title}\n{policy_text}"
    )
    if audience == "merchant_draft":
        user += "\n\nBu yanıt satıcının onayından sonra gönderilecek bir taslaktır."
    return system, user


def stream_reply(system: str, user: str, model: str | None = None, timeout_sec: int = 120) -> Iterator[str]:
    """Yields text chunks from the local Ollama model. Raises on connection failure."""
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": True,
        "options": {"temperature": 0.3, "num_predict": 320},
    }
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        for line in resp:
            if not line.strip():
                continue
            chunk = json.loads(line.decode("utf-8"))
            text = chunk.get("message", {}).get("content", "")
            if text:
                yield text
            if chunk.get("done"):
                break


_NUM = re.compile(r"\d+(?:[.,]\d+)?")


def ungrounded_numbers(reply: str, *sources: str) -> list[str]:
    """Numbers in the reply that appear in none of the sources (policy text, customer message)."""
    allowed = {n.replace(",", ".") for src in sources for n in _NUM.findall(src or "")}
    return [n for n in _NUM.findall(reply) if n.replace(",", ".") not in allowed]


def grounded_reply(
    system: str,
    user: str,
    policy_text: str,
    message: str,
    model: str | None,
) -> dict[str, Any]:
    """
    Generates a reply and rejects it if it states numbers (days, amounts, codes) that
    the policy does not contain. Retries once with a stricter instruction, then gives up
    so the caller can fall back to the rule-based template.
    """
    attempts = []
    prompts = [
        user,
        user + "\n\nÖNEMLİ: Kuralda geçmeyen hiçbir sayı yazma. Sayı gerekiyorsa kuraldaki sayıyı aynen kullan.",
    ]
    for prompt in prompts:
        t0 = time.perf_counter()
        text = re.sub(r"\s+", " ", "".join(stream_reply(system, prompt, model))).strip()
        bad = ungrounded_numbers(text, policy_text, message)
        attempts.append({"ms": round((time.perf_counter() - t0) * 1000), "ungrounded": bad})
        if text and not bad:
            return {"text": text, "grounded": True, "attempts": attempts}
    return {"text": None, "grounded": False, "attempts": attempts}


def installed_models(timeout_sec: float = 1.5) -> list[str]:
    """Names of models available in the local Ollama, or [] if it is not running."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=timeout_sec) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def pick_model(requested: str | None, available: list[str]) -> str | None:
    """Requested model if installed, else the configured default, else the first installed one."""
    for name in (requested, DEFAULT_MODEL):
        if name and name in available:
            return name
    return available[0] if available else None


def warm_up() -> dict[str, Any]:
    """Loads the heavy local models once so the first customer does not wait."""
    t0 = time.perf_counter()
    order: OrderFeatures = {
        "order_id": "WARMUP", "order_amount_tl": 500.0, "delivery_days": 2,
        "past_orders_count": 3, "past_returns_count": 0,
        "unboxing_video_available": True, "box_damaged_reported": False,
    }
    res = analyze_message("Kargom ne zaman gelir?", order)
    return {"seconds": round(time.perf_counter() - t0, 1), "models": res["models"]}
