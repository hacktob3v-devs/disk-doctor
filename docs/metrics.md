# EsnafDoktor — Ölçülmüş Metrikler

**Tarih:** 18.10.2026
**Üreten:** `python scripts/evaluate_honest_metrics.py` — bu dosyadaki tüm sayılar bu betik tarafından ölçülür, elle yazılmış değer yoktur.
**Ortam:** Analiz hattı (NLU, RAG, risk) CPU üzerinde. Yanıt modeli (Gemma 3 4B, Ollama) bu betikte ölçülmez; README'deki yanıt süreleri ayrı ölçülmüştür.
**Bu çalıştırmada:** NLU = `Calibrated-Turkish-NLU (Zero-Latency Rule-Enhanced)`, Cross-Encoder = açık, risk = `calibrated_rf_fallback`.

---

## 1. Sınıflandırma — 20 vakalık ayrılmış test seti (`data/holdout_gold.jsonl`)

| Görev | Doğruluk | Macro Precision | Macro Recall | Macro F1 |
| :--- | :---: | :---: | :---: | :---: |
| **Kategori — sistem** (eşleşen kuralın kategorisi) | **%95.0** | %96.0 | %93.3 | **%93.8** |
| Kategori — sadece anahtar kelime NLU | %60.0 | %51.4 | %60.3 | %54.0 |
| Niyet — anahtar kelime NLU | %60.0 | %82.2 | %62.1 | %61.2 |

> İnce ayarlı BERTurk modelleri bu repoda yer almadığı için NLU anahtar kelime yedeğiyle çalışır. Arayüzde gösterilen kategori, kural düzeyinde daha isabetli olan RAG eşleşmesinden alınır.

---

## 2. Kural getirme ablasyonu

Kural düzeyi: 21 günlük dil müşteri mesajı, doğru cevap tek bir politika (`scripts/evaluate_rag_policy.py`).
Kategori düzeyi: 20 vakalık test seti; doğru kategoriden herhangi bir politika isabet sayılır.

| Getirme yöntemi | Kural Hit@1 | Kural Hit@3 | Kural MRR@3 | Kategori Hit@1 | Kategori Hit@3 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| BM25 tek başına (Türkçe normalize) | %81.0 | %95.2 | 0.865 | %75.0 | %90.0 |
| multilingual-e5-small tek başına | %71.4 | %85.7 | 0.786 | %95.0 | %100.0 |
| Hibrit: BM25 + E5 + RRF (k=60) | %81.0 | %95.2 | 0.873 | %90.0 | %90.0 |
| **Hibrit + anahtar kelime + Cross-Encoder ağırlığı (sistem)** | **%95.2** | %100.0 | 0.976 | %100.0 | %100.0 |

---

## 3. Süre (ısınmış, medyan, CPU)

* **NLU:** `0.06 ms`
* **Kural getirme (BM25 + E5 + Cross-Encoder):** `439 ms`
* **Risk skoru:** `0.04 ms` (`calibrated_rf_fallback`)
* **Analizin tamamı (arayüzdeki `/api/analyze`):** `423 ms`
* **Değişken API maliyeti:** `0.00 TL` — tüm modeller yerelde çalışır

---

## 4. Karışıklık matrisi — sistem kategorisi

Satır: doğru, sütun: tahmin. Sınıflar: `['genel', 'iade', 'kargo', 'teknik', 'urun']`
```
[[2 0 1 0 0]
 [0 5 0 0 0]
 [0 0 4 0 0]
 [0 0 0 4 0]
 [0 0 0 0 4]]
```
