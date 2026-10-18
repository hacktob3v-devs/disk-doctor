"""
EsnafDoktor - Honest & Leakage-Free Evaluation Harness
Hacktoberfest Elazığ 2026 - Week 2 "Side Hustle"

Measures, on this machine and this code:
  - keyword NLU category/intent on the 20-case held-out gold set
  - system category (as shown in the interface: taken from the matched policy)
  - retrieval ablation (BM25 / E5 / RRF / final re-ranker), category-level on the
    gold set and exact-policy-level on the colloquial set of evaluate_rag_policy.py
  - warm latencies
Every number written to docs/metrics.md is computed here; nothing is hard-coded.

Usage: python scripts/evaluate_honest_metrics.py
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

# Force UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np  # noqa: E402
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support  # noqa: E402

from core.assistant import analyze_message  # noqa: E402
from core.contracts import OrderFeatures  # noqa: E402
from core.nlu_berturk import classify_text  # noqa: E402
from core.rag_engine import get_rag_engine, retrieve_policies  # noqa: E402
from core.tabpfn_dispute import evaluate_order_risk  # noqa: E402
from scripts.evaluate_rag_policy import CASES as POLICY_CASES  # noqa: E402

GOLD_PATH = ROOT_DIR / "data" / "holdout_gold.jsonl"
METRICS_MD = ROOT_DIR / "docs" / "metrics.md"

ORDER: OrderFeatures = {
    "order_id": "TEST-BENCH",
    "order_amount_tl": 1200.0,
    "delivery_days": 3,
    "past_orders_count": 5,
    "past_returns_count": 1,
    "unboxing_video_available": True,
    "box_damaged_reported": False,
}

STRATEGIES = [
    ("bm25", "BM25 tek başına (Türkçe normalize)"),
    ("dense", "multilingual-e5-small tek başına"),
    ("rrf", "Hibrit: BM25 + E5 + RRF (k=60)"),
    ("final", "Hibrit + anahtar kelime + Cross-Encoder ağırlığı (sistem)"),
]


def policy_category(policy_id: str) -> str:
    return policy_id.split("_")[1].lower()  # POL_IADE_03 -> iade


def ranked_policy_ids(engine, query: str, strategy: str) -> list[str]:
    if strategy == "final":
        res = engine.retrieve(query, top_k=len(engine.policies))
        return [e["policy_id"] for e in res["top_evidences"]]
    bm25 = np.array(engine.bm25.score(query))
    dense = np.array(engine.dense.score(query))
    if strategy == "bm25":
        order = np.argsort(-bm25, kind="stable")
    elif strategy == "dense":
        order = np.argsort(-dense, kind="stable")
    else:
        rb = {i: r for r, i in enumerate(np.argsort(-bm25, kind="stable"))}
        rd = {i: r for r, i in enumerate(np.argsort(-dense, kind="stable"))}
        rrf = np.array([1 / (60 + rb[i]) + 1 / (60 + rd[i]) for i in range(len(engine.policies))])
        order = np.argsort(-rrf, kind="stable")
    return [engine.policies[i]["id"] for i in order]


def hit_stats(ranks: list[int | None]) -> tuple[float, float, float]:
    """ranks: 1-based rank of the first correct item, or None."""
    n = len(ranks)
    hit1 = sum(1 for r in ranks if r == 1) / n * 100
    hit3 = sum(1 for r in ranks if r is not None and r <= 3) / n * 100
    mrr3 = float(np.mean([1 / r if r is not None and r <= 3 else 0.0 for r in ranks]))
    return hit1, hit3, mrr3


def run_evaluation():
    print("=" * 65)
    print(">> ESNAFDOKTOR: HONEST BENCHMARK HARNESS")
    print("=" * 65)

    with open(GOLD_PATH, "r", encoding="utf-8") as f:
        gold = [json.loads(line) for line in f if line.strip()]
    print(f"Loaded {len(gold)} held-out gold cases, {len(POLICY_CASES)} policy-labelled cases.")

    engine = get_rag_engine()
    analyze_message("ısınma", ORDER)  # load models before timing

    y_true_kat, y_nlu_kat, y_sys_kat = [], [], []
    y_true_niyet, y_nlu_niyet = [], []
    lat_nlu, lat_rag, lat_risk, lat_total = [], [], [], []
    cat_ranks = {s: [] for s, _ in STRATEGIES}

    for item in gold:
        txt = item["text"]
        y_true_kat.append(item["expected_kategori"])
        y_true_niyet.append(item["expected_niyet"])

        t0 = time.perf_counter()
        nlu = classify_text(txt)
        lat_nlu.append((time.perf_counter() - t0) * 1000)
        y_nlu_kat.append(nlu["category"])
        y_nlu_niyet.append(nlu["intent"])

        t0 = time.perf_counter()
        retrieve_policies(txt, top_k=3)
        lat_rag.append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        evaluate_order_risk(ORDER, sentiment_score=nlu["sentiment_score"])
        lat_risk.append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        y_sys_kat.append(analyze_message(txt, ORDER)["category"])
        lat_total.append((time.perf_counter() - t0) * 1000)

        for s, _ in STRATEGIES:
            cats = [policy_category(p) for p in ranked_policy_ids(engine, txt, s)]
            cat_ranks[s].append(cats.index(item["expected_kategori"]) + 1 if item["expected_kategori"] in cats else None)

    pol_ranks = {s: [] for s, _ in STRATEGIES}
    for txt, expected in POLICY_CASES:
        for s, _ in STRATEGIES:
            ids = ranked_policy_ids(engine, txt, s)
            pol_ranks[s].append(ids.index(expected) + 1)

    def prf(y_true, y_pred):
        p, r, f, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
        return accuracy_score(y_true, y_pred) * 100, p * 100, r * 100, f * 100

    nlu_kat = prf(y_true_kat, y_nlu_kat)
    sys_kat = prf(y_true_kat, y_sys_kat)
    nlu_niyet = prf(y_true_niyet, y_nlu_niyet)
    labels = sorted(set(y_true_kat + y_sys_kat))
    cm = confusion_matrix(y_true_kat, y_sys_kat, labels=labels)

    med = statistics.median
    risk_method = evaluate_order_risk(ORDER)["method"]
    nlu_model = classify_text("test")["model_name"]
    reranker = "açık" if engine.reranker_model is not None else "kapalı"

    print(f"\nKategori, sistem:      doğruluk %{sys_kat[0]:.1f} | macro F1 %{sys_kat[3]:.1f}")
    print(f"Kategori, sadece NLU:  doğruluk %{nlu_kat[0]:.1f} | macro F1 %{nlu_kat[3]:.1f}")
    print(f"Niyet, NLU:            doğruluk %{nlu_niyet[0]:.1f} | macro F1 %{nlu_niyet[3]:.1f}")
    for s, name in STRATEGIES:
        c = hit_stats(cat_ranks[s])
        p = hit_stats(pol_ranks[s])
        print(f"{name:58s} kategori Hit@1 %{c[0]:.1f} | kural Hit@1 %{p[0]:.1f}")
    print(f"Süre (medyan): NLU {med(lat_nlu):.2f} ms | RAG {med(lat_rag):.0f} ms | risk {med(lat_risk):.2f} ms | analiz {med(lat_total):.0f} ms")

    rows = []
    for s, name in STRATEGIES:
        c = hit_stats(cat_ranks[s])
        p = hit_stats(pol_ranks[s])
        bold = "**" if s == "final" else ""
        rows.append(
            f"| {bold}{name}{bold} | {bold}%{p[0]:.1f}{bold} | %{p[1]:.1f} | {p[2]:.3f} | %{c[0]:.1f} | %{c[1]:.1f} |"
        )
    ablation = "\n".join(rows)

    md = f"""# EsnafDoktor — Ölçülmüş Metrikler

**Tarih:** {time.strftime("%d.%m.%Y")}
**Üreten:** `python scripts/evaluate_honest_metrics.py` — bu dosyadaki tüm sayılar bu betik tarafından ölçülür, elle yazılmış değer yoktur.
**Ortam:** Analiz hattı (NLU, RAG, risk) CPU üzerinde. Yanıt modeli (Gemma 3 4B, Ollama) bu betikte ölçülmez; README'deki yanıt süreleri ayrı ölçülmüştür.
**Bu çalıştırmada:** NLU = `{nlu_model}`, Cross-Encoder = {reranker}, risk = `{risk_method}`.

---

## 1. Sınıflandırma — 20 vakalık ayrılmış test seti (`data/holdout_gold.jsonl`)

| Görev | Doğruluk | Macro Precision | Macro Recall | Macro F1 |
| :--- | :---: | :---: | :---: | :---: |
| **Kategori — sistem** (eşleşen kuralın kategorisi) | **%{sys_kat[0]:.1f}** | %{sys_kat[1]:.1f} | %{sys_kat[2]:.1f} | **%{sys_kat[3]:.1f}** |
| Kategori — sadece anahtar kelime NLU | %{nlu_kat[0]:.1f} | %{nlu_kat[1]:.1f} | %{nlu_kat[2]:.1f} | %{nlu_kat[3]:.1f} |
| Niyet — anahtar kelime NLU | %{nlu_niyet[0]:.1f} | %{nlu_niyet[1]:.1f} | %{nlu_niyet[2]:.1f} | %{nlu_niyet[3]:.1f} |

> İnce ayarlı BERTurk modelleri bu repoda yer almadığı için NLU anahtar kelime yedeğiyle çalışır. Arayüzde gösterilen kategori, kural düzeyinde daha isabetli olan RAG eşleşmesinden alınır.

---

## 2. Kural getirme ablasyonu

Kural düzeyi: {len(POLICY_CASES)} günlük dil müşteri mesajı, doğru cevap tek bir politika (`scripts/evaluate_rag_policy.py`).
Kategori düzeyi: 20 vakalık test seti; doğru kategoriden herhangi bir politika isabet sayılır.

| Getirme yöntemi | Kural Hit@1 | Kural Hit@3 | Kural MRR@3 | Kategori Hit@1 | Kategori Hit@3 |
| :--- | :---: | :---: | :---: | :---: | :---: |
{ablation}

---

## 3. Süre (ısınmış, medyan, CPU)

* **NLU:** `{med(lat_nlu):.2f} ms`
* **Kural getirme (BM25 + E5 + Cross-Encoder):** `{med(lat_rag):.0f} ms`
* **Risk skoru:** `{med(lat_risk):.2f} ms` (`{risk_method}`)
* **Analizin tamamı (arayüzdeki `/api/analyze`):** `{med(lat_total):.0f} ms`
* **Değişken API maliyeti:** `0.00 TL` — tüm modeller yerelde çalışır

---

## 4. Karışıklık matrisi — sistem kategorisi

Satır: doğru, sütun: tahmin. Sınıflar: `{labels}`
```
{cm}
```
"""
    METRICS_MD.parent.mkdir(parents=True, exist_ok=True)
    METRICS_MD.write_text(md, encoding="utf-8")
    print(f"\n✅ Metrics exported to: {METRICS_MD}")


if __name__ == "__main__":
    run_evaluation()
