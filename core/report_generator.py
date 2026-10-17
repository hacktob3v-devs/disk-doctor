"""
EsnafDoktor - Printable Merchant/Customer Resolution Report Generator
Hacktoberfest Elazığ 2026 - Week 2 "Side Hustle"

Generates clean, printable A4 HTML reports and markdown summaries
demonstrating 100% offline execution, 0.00 TL API cost, and grounded citations.
"""
from __future__ import annotations

import datetime

from core.contracts import ActionCard, NLUResult, OrderFeatures, RAGResult, TabularRiskResult


def generate_printable_html_report(
    merchant_name: str,
    customer_message: str,
    order: OrderFeatures,
    nlu: NLUResult,
    rag: RAGResult,
    risk: TabularRiskResult,
    action: ActionCard,
    total_time_s: float,
) -> str:
    """Produces a responsive, printable A4 HTML certificate for the merchant's archive."""
    now_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    risk_color = "#10b981" if risk["risk_level"] == "green" else (
        "#f59e0b" if risk["risk_level"] == "yellow" else "#ef4444"
    )
    risk_text = "DÜŞÜK RİSK (GÜVENLİ)" if risk["risk_level"] == "green" else (
        "ORTA RİSK (İNCELEME GEREKLİ)" if risk["risk_level"] == "yellow" else "YÜKSEK RİSK (ŞÜPHELİ / DİKKAT)"
    )

    evidences_html = ""
    for ev in rag["top_evidences"][:2]:
        evidences_html += f"""
        <div style="background: #f8fafc; border-left: 4px solid #3b82f6; padding: 10px 14px; margin-bottom: 8px; border-radius: 4px;">
            <div style="font-weight: 600; color: #1e293b; font-size: 13px;">[{ev['policy_id']}] {ev['title']}</div>
            <div style="font-size: 12px; color: #475569; margin-top: 4px;">{ev['content']}</div>
            <div style="font-size: 11px; color: #94a3b8; margin-top: 4px;">BM25 Sıra: #{ev['bm25_rank']} | Yoğun Vektör Sıra: #{ev['dense_rank']} | RRF Skoru: {ev['rrf_score']}</div>
        </div>
        """

    instructions_html = "".join([f"<li style='margin-bottom: 4px;'>{inst}</li>" for inst in action["merchant_instructions"]])
    factors_html = "".join([f"<li>{fac}</li>" for fac in risk["risk_factors"]])

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<title>EsnafDoktor Çözüm Raporu - {order['order_id']}</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #0f172a; margin: 0; padding: 24px; background: #fff; }}
    .header {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 700; color: #fff; }}
    .banner {{ background: #0f172a; color: #f8fafc; padding: 8px 16px; border-radius: 6px; font-size: 12px; display: flex; justify-content: space-between; margin-bottom: 20px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }}
    .card {{ border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; background: #ffffff; }}
    .card-title {{ font-size: 13px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 8px; }}
    .reply-box {{ background: #f0fdf4; border: 1px solid #bbf7d0; padding: 12px 16px; border-radius: 6px; font-size: 13px; color: #166534; line-height: 1.5; }}
    @media print {{ body {{ padding: 0; }} .no-print {{ display: none; }} }}
</style>
</head>
<body>

<div class="banner">
    <span>🔒 <strong>%100 ÇEVRİMDIŞI & YEREL MOTOR</strong> (Gemma 4 + BERTurk + TabPFN)</span>
    <span>⚡ Toplam Süre: <strong>{total_time_s:.3f} sn</strong></span>
    <span>💰 API Maliyeti: <strong>0.00 TL</strong></span>
</div>

<div class="header">
    <div>
        <h1 style="margin: 0; font-size: 22px; color: #0f172a;">{merchant_name} — Müşteri İade & Uyuşmazlık Raporu</h1>
        <div style="font-size: 12px; color: #64748b; margin-top: 4px;">Sipariş No: <strong>{order['order_id']}</strong> | Düzenlenme Tarihi: {now_str}</div>
    </div>
    <div style="text-align: right;">
        <span class="badge" style="background-color: {risk_color};">{risk_text}</span>
        <div style="font-size: 11px; color: #64748b; margin-top: 4px;">TabPFN Risk: %{int(risk['risk_score']*100)}</div>
    </div>
</div>

<div class="grid">
    <div class="card">
        <div class="card-title">Müşteri Şikayeti & NLU Sınıflandırması</div>
        <p style="font-size: 13px; color: #1e293b; background: #f8fafc; padding: 10px; border-radius: 6px; font-style: italic; margin-top: 0;">
            "{customer_message}"
        </p>
        <div style="font-size: 12px; color: #334155;">
            <strong>Kategori:</strong> {nlu['category'].upper()} (%{int(nlu['category_confidence']*100)})<br>
            <strong>Niyet/Ton:</strong> {nlu['intent'].upper()} (Duygu Skoru: {nlu['sentiment_score']})<br>
            <strong>Model:</strong> {nlu['model_name']}
        </div>
    </div>

    <div class="card">
        <div class="card-title">Sipariş & Tabular Risk Analizi (TabPFN)</div>
        <div style="font-size: 12px; color: #334155; line-height: 1.6;">
            <strong>Sipariş Tutarı:</strong> {order['order_amount_tl']:,.2f} TL<br>
            <strong>Teslimat Süresi:</strong> {order['delivery_days']} gün | <strong>Geçmiş İade:</strong> {order['past_returns_count']} / {order['past_orders_count']} sipariş<br>
            <strong>Kutu Hasarlı Mı:</strong> {'Evet' if order['box_damaged_reported'] else 'Hayır'} | <strong>Açılış Videosu:</strong> {'Var' if order['unboxing_video_available'] else 'Yok'}<br>
        </div>
        <ul style="font-size: 11px; color: #b91c1c; margin: 6px 0 0 0; padding-left: 18px;">
            {factors_html}
        </ul>
    </div>
</div>

<div class="card" style="margin-bottom: 20px;">
    <div class="card-title">Dayanak Mağaza Politikaları (2026 Hibrit RAG Kanıtları)</div>
    {evidences_html}
</div>

<div class="card" style="margin-bottom: 20px;">
    <div class="card-title">Esnaf Eylem Planı (Öncelik: {action['priority'].upper()})</div>
    <div style="font-weight: 700; color: #0f172a; font-size: 14px; margin-bottom: 6px;">
        👉 {action['suggested_action']}
    </div>
    <ol style="font-size: 13px; color: #334155; margin: 0; padding-left: 20px;">
        {instructions_html}
    </ol>
</div>

<div class="card">
    <div class="card-title">Müşteriye Gönderilmeye Hazır Yanıt Taslağı</div>
    <div class="reply-box">
        {action['customer_reply_tr']}
    </div>
</div>

<div style="margin-top: 24px; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #f1f5f9; padding-top: 12px;">
    EsnafDoktor © 2026 — Hacktoberfest Elazığ Açık Kaynak Yapay Zeka Projesi | Tamamen yerel çalışır, müşteri verisi cihazdan çıkmaz.
</div>

</body>
</html>
"""
    return html
