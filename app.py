"""
EsnafDoktor - Presentation Mode Interface
Hacktoberfest Elazığ 2026 - Week 2 "Side Hustle"

Designed for a high-impact, ultra-clean 3-minute live pitch to the jury.
Minimalist layout: 4 Instant Scenarios -> Input & Telemetry -> Gemma Decision & Ready Reply.
100% Offline, Zero AI Slop, Zero Clutter.
"""
from __future__ import annotations

import json
import socket
import time
import urllib.parse
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from core.contracts import OrderFeatures
from core.llm_gemma import generate_action_card
from core.nlu_berturk import classify_text
from core.rag_engine import retrieve_policies
from core.report_generator import generate_printable_html_report
from core.tabpfn_dispute import evaluate_order_risk

ROOT_DIR = Path(__file__).resolve().parent
DEMO_PATH = ROOT_DIR / "data" / "demo_cases.json"

st.set_page_config(
    page_title="EsnafDoktor | Canlı Sunum Ekranı",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------- CLEAN PRESENTATION STYLING -----------------
st.markdown("""
<style>
    /* Clean Minimalist Typography */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
    }

    /* Main Presentation Hero */
    .pitch-header {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .pitch-title {
        font-size: 24px;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .pitch-subtitle {
        font-size: 13px;
        color: #64748b;
        margin-top: 3px;
    }

    /* Stage Presentation Card */
    .decision-banner {
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 14px;
        color: #ffffff;
    }
    .reply-box {
        background: #ffffff;
        border: 1.5px solid #e2e8f0;
        border-radius: 8px;
        padding: 14px 18px;
        font-size: 14px;
        line-height: 1.6;
        color: #1e293b;
        margin-bottom: 14px;
    }
</style>
""", unsafe_allow_html=True)


def check_internet(timeout=0.2) -> bool:
    """Rapid socket probe to verify offline status live on stage."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except (socket.timeout, OSError):
        return False


# Load demo cases
with open(DEMO_PATH, "r", encoding="utf-8") as f:
    DEMO_CASES = json.load(f)

is_online = check_internet()
wifi_label = "🌐 Çevrimiçi" if is_online else "🔒 %100 ÇEVRİMDIŞI (Wi-Fi Kapalı)"
wifi_color = "#64748b" if is_online else "#15803d"

# Top Presentation Header
st.markdown(f"""
<div class="pitch-header">
    <div>
        <h1 class="pitch-title">🏪 EsnafDoktor — Canlı Teşhis & Sunum Masası</h1>
        <div class="pitch-subtitle">E-Ticaret & KOBİ Satıcıları İçin Çevrimdışı Yapay Zekâ (Gemma 4 + BERTurk + TabPFN) Uyuşmazlık ve İade Copilotu</div>
    </div>
    <div style="text-align: right;">
        <span style="background: #f1f5f9; color: {wifi_color}; font-weight: 800; font-size: 12px; padding: 6px 12px; border-radius: 9999px; border: 1px solid #cbd5e1;">
            {wifi_label}
        </span>
        <div style="font-size: 12px; color: #64748b; margin-top: 5px;">Değişken API Maliyeti: <strong style="color: #15803d;">0.00 TL</strong></div>
    </div>
</div>
""", unsafe_allow_html=True)

# 4 Presentation Scenarios Across The Top
st.markdown("##### 📌 Canlı Sunum Senaryoları (Jüriye Göstermek İçin Tek Tıkla Seçin)")
sc_cols = st.columns(4)

labels = [
    "📦 1. Kargo Hasarı (Kırık Kupa)",
    "🚨 2. Şüpheli İade (5.800 TL Mont)",
    "🟢 3. Beden Değişimi (Sadık Alıcı)",
    "⭐ 4. Hızlı Teslimat (Teşekkür)"
]

for idx, col in enumerate(sc_cols):
    if col.button(labels[idx], key=f"pitch_case_{idx}", use_container_width=True):
        st.session_state.p_msg = DEMO_CASES[idx]["customer_message"]
        st.session_state.p_oid = DEMO_CASES[idx]["order"]["order_id"]
        st.session_state.p_amt = float(DEMO_CASES[idx]["order"]["order_amount_tl"])
        st.session_state.p_days = int(DEMO_CASES[idx]["order"]["delivery_days"])
        st.session_state.p_past_o = int(DEMO_CASES[idx]["order"]["past_orders_count"])
        st.session_state.p_past_r = int(DEMO_CASES[idx]["order"]["past_returns_count"])
        st.session_state.p_unbox = bool(DEMO_CASES[idx]["order"]["unboxing_video_available"])
        st.session_state.p_dam = bool(DEMO_CASES[idx]["order"]["box_damaged_reported"])
        st.rerun()

# Check query parameters for speech-to-text input from browser
if "voice_input" in st.query_params:
    v_in = st.query_params.get("voice_input", "")
    if v_in:
        st.session_state.p_msg = v_in
    del st.query_params["voice_input"]

# Default session values
if "p_msg" not in st.session_state:
    st.session_state.p_msg = DEMO_CASES[0]["customer_message"]
    st.session_state.p_oid = DEMO_CASES[0]["order"]["order_id"]
    st.session_state.p_amt = float(DEMO_CASES[0]["order"]["order_amount_tl"])
    st.session_state.p_days = int(DEMO_CASES[0]["order"]["delivery_days"])
    st.session_state.p_past_o = int(DEMO_CASES[0]["order"]["past_orders_count"])
    st.session_state.p_past_r = int(DEMO_CASES[0]["order"]["past_returns_count"])
    st.session_state.p_unbox = bool(DEMO_CASES[0]["order"]["unboxing_video_available"])
    st.session_state.p_dam = bool(DEMO_CASES[0]["order"]["box_damaged_reported"])

if "auto_speak" not in st.session_state:
    st.session_state.auto_speak = False

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Main Stage: 2 Clean Presentation Columns
col_input, col_result = st.columns([1.1, 1.4])

with col_input:
    st.markdown("#### 1. Müşteri Talebi & Sesli Girdi")

    # Interactive Speech-to-Text (STT) Voice Assistant Widget
    components.html("""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <button id="micBtn" onclick="toggleSTT()" style="background: #2563eb; color: white; border: none; width: 38px; height: 38px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 18px; box-shadow: 0 2px 4px rgba(37,99,235,0.2);">
                🎙️
            </button>
            <div>
                <div id="sttStatus" style="font-weight: 700; font-size: 13px; color: #1e293b;">Sesli Asistan: Mikrofona Konuş</div>
                <div id="sttSub" style="font-size: 11px; color: #64748b;">Türkçe müşteri mesajını sesli iletmek için butona tıklayın.</div>
            </div>
        </div>
        <div id="pulseBadge" style="display: none; background: #fee2e2; color: #b91c1c; font-size: 11px; font-weight: 700; padding: 4px 8px; border-radius: 12px;">
            🔴 DİNLİYOR...
        </div>
    </div>

    <script>
    var recognizing = false;
    var recognition = null;

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        var SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRec();
        recognition.lang = 'tr-TR';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = function() {
            recognizing = true;
            document.getElementById('micBtn').style.background = '#dc2626';
            document.getElementById('pulseBadge').style.display = 'block';
            document.getElementById('sttStatus').innerText = 'Dinleniyor... Şimdi Konuşun';
            document.getElementById('sttSub').innerText = 'Örn: "Kargom kırık geldi paramı iade edin"';
        };

        recognition.onresult = function(event) {
            var text = event.results[0][0].transcript;
            document.getElementById('sttStatus').innerText = 'Algılandı: "' + text.substring(0, 30) + '..."';
            document.getElementById('sttSub').innerText = 'Sistem kararı hesaplanıyor...';
            // Send back to Streamlit via parent query param reload
            window.parent.location.search = '?voice_input=' + encodeURIComponent(text);
        };

        recognition.onerror = function(event) {
            recognizing = false;
            document.getElementById('micBtn').style.background = '#2563eb';
            document.getElementById('pulseBadge').style.display = 'none';
            document.getElementById('sttStatus').innerText = 'Hata: ' + event.error;
        };

        recognition.onend = function() {
            recognizing = false;
            document.getElementById('micBtn').style.background = '#2563eb';
            document.getElementById('pulseBadge').style.display = 'none';
        };
    } else {
        document.getElementById('sttStatus').innerText = 'Tarayıcıda Web Speech API desteği yok.';
    }

    function toggleSTT() {
        if (!recognition) {
            alert('Tarayıcınız Web Speech API desteklemiyor. Lütfen Chrome veya Edge kullanın.');
            return;
        }
        if (recognizing) {
            recognition.stop();
        } else {
            recognition.start();
        }
    }
    </script>
    """, height=65)

    cur_msg = st.text_area(
        "Müşterinin Yazılı Mesajı:",
        value=st.session_state.p_msg,
        height=130
    )

    with st.expander("Sipariş Bilgilerini Düzenle (Tablo Verisi)", expanded=False):
        c1, c2 = st.columns(2)
        v_oid = c1.text_input("Sipariş No", value=st.session_state.p_oid)
        v_amt = c2.number_input("Tutar (TL)", value=st.session_state.p_amt, step=100.0)
        c3, c4 = st.columns(2)
        v_days = c3.number_input("Kargo Süresi (Gün)", value=st.session_state.p_days)
        v_past_o = c4.number_input("Geçmiş Sipariş", value=st.session_state.p_past_o)
        c5, c6 = st.columns(2)
        v_past_r = c5.number_input("Geçmiş İade", value=st.session_state.p_past_r)
        v_unbox = c6.checkbox("Açılış Videosu Var", value=st.session_state.p_unbox)
        v_dam = st.checkbox("Paket Hasarlı Bildirildi", value=st.session_state.p_dam)

    col_btn, col_auto_tts = st.columns([1.3, 1.1])
    with col_btn:
        btn_eval = st.button("⚡ Analiz Et & Karar Ver (Gemma 4)", type="primary", use_container_width=True)
    with col_auto_tts:
        st.session_state.auto_speak = st.checkbox("🔊 Otomatik Seslendir", value=st.session_state.auto_speak)

with col_result:
    st.markdown("#### 2. Gemma 4 Kararı ve Aksiyon Planı")

    t_start = time.perf_counter()

    order_obj: OrderFeatures = {
        "order_id": st.session_state.p_oid,
        "order_amount_tl": float(st.session_state.p_amt),
        "delivery_days": int(st.session_state.p_days),
        "past_orders_count": int(st.session_state.p_past_o),
        "past_returns_count": int(st.session_state.p_past_r),
        "unboxing_video_available": st.session_state.p_unbox,
        "box_damaged_reported": st.session_state.p_dam,
    }

    # Run pipeline
    nlu_res = classify_text(cur_msg)
    rag_res = retrieve_policies(cur_msg, top_k=2)
    risk_res = evaluate_order_risk(order_obj, sentiment_score=nlu_res["sentiment_score"])
    action_res = generate_action_card("E-Ticaret Butik Satıcısı", cur_msg, nlu_res, rag_res, risk_res)

    latency_s = time.perf_counter() - t_start

    # Clean Badges Row
    r_color = "#15803d" if risk_res["risk_level"] == "green" else (
        "#b45309" if risk_res["risk_level"] == "yellow" else "#b91c1c"
    )
    r_title = "GÜVENLİ (%s)" % int(risk_res["risk_score"]*100) if risk_res["risk_level"] == "green" else (
        "İNCELEME GEREKLİ (%s)" % int(risk_res["risk_score"]*100) if risk_res["risk_level"] == "yellow" else "YÜKSEK RİSK (%s)" % int(risk_res["risk_score"]*100)
    )

    b1, b2, b3 = st.columns(3)
    b1.markdown(f"**Kategori:** `{nlu_res['category'].upper()}`")
    b2.markdown(f"**TabPFN Riski:** <span style='color:{r_color}; font-weight:800;'>{r_title}</span>", unsafe_allow_html=True)
    b3.markdown(f"**Öncelik:** `{action_res['priority'].upper()}`")

    # Big Direct Decision Banner
    st.markdown(f"""
    <div class="decision-banner" style="background-color: {r_color};">
        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.9;">Gemma 4 Önerilen Aksiyon Kararı</div>
        <div style="font-size: 18px; font-weight: 800; margin-top: 4px;">{action_res['suggested_action']}</div>
        <div style="font-size: 12px; margin-top: 4px; opacity: 0.9;">Dayanak Kural: {action_res['grounded_rule']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Customer Reply Box
    st.markdown("**Müşteriye Hazır Türkçe Yanıt (WhatsApp / Trendyol):**")
    st.markdown(f"""
    <div class="reply-box">
        {action_res['customer_reply_tr']}
    </div>
    """, unsafe_allow_html=True)

    # Action Buttons: WhatsApp + TTS Voice + Printable Report
    a_col1, a_col2, a_col3 = st.columns([1.1, 1.1, 1.2])

    # WhatsApp Link
    wa_encoded = urllib.parse.quote(action_res["customer_reply_tr"])
    a_col1.markdown(f"""
    <a href="https://api.whatsapp.com/send?text={wa_encoded}" target="_blank" style="text-decoration: none;">
        <div style="background: #25d366; color: white; text-align: center; padding: 8px 12px; border-radius: 6px; font-weight: 700; font-size: 13px;">
            💬 WhatsApp ile Gönder
        </div>
    </a>
    """, unsafe_allow_html=True)

    # Text-to-Speech (TTS) Voice Engine
    v_clean = action_res["voice_summary_tr"].replace("'", "\\'").replace('"', '\\"')
    auto_speak_js = "true" if st.session_state.auto_speak else "false"

    with a_col2:
        components.html(f"""
        <button id="ttsBtn" onclick="speakText()" style="width: 100%; background: #0f172a; color: white; border: none; padding: 8px 12px; border-radius: 6px; font-weight: 700; font-size: 13px; cursor: pointer;">
            🔊 Asistan Kararını Oku
        </button>
        <script>
        var autoPlay = {auto_speak_js};
        function speakText() {{
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                var u = new SpeechSynthesisUtterance("{v_clean}");
                u.lang = 'tr-TR';
                u.rate = 1.05;
                window.speechSynthesis.speak(u);
            }}
        }}
        if (autoPlay) {{
            window.addEventListener('load', function() {{
                setTimeout(speakText, 300);
            }});
        }}
        </script>
        """, height=38)

    # HTML Report Download
    rep_html = generate_printable_html_report(
        "E-Ticaret Butik Mağazası", cur_msg, order_obj, nlu_res, rag_res, risk_res, action_res, latency_s
    )
    a_col3.download_button(
        "📄 A4 Servis Raporu",
        data=rep_html,
        file_name=f"Rapor_{order_obj['order_id']}.html",
        mime="text/html",
        use_container_width=True
    )

st.markdown("<hr style='margin: 20px 0 14px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

# Bottom Collapsible Jury Evidence & Slide 18 Table
with st.expander("🏆 Fırat Üniversitesi Jürisi İçin Bilimsel Kanıtlar & Slayt 18 Tablosu", expanded=False):
    t_c1, t_c2 = st.columns(2)
    with t_c1:
        st.markdown("**1. Neden Açık Kaynak Kapalı API'den (GPT-4o) Üstün? (Slayt 18)**")
        st.markdown("""
        | Kriter | Kapalı API (OpenAI) | EsnafDoktor (Yerel) |
        | :--- | :--- | :--- |
        | **Maliyet** | $0.05 / çağrı (~15.000 TL/ay) | **0.00 TL (Sıfır maliyet)** |
        | **İnternet** | Kesilince çalışmaz | **%100 Çevrimdışı (Wi-Fi kapalı)** |
        | **Gizlilik** | Müşteri verisi buluta gider | **Sıfır sızıntı (Dükkan laptopunda)** |
        | **Tablo Verisi** | Sayı uydurur | **TabPFN ile 18 ms kesin risk hesabı** |
        """)
    with t_c2:
        st.markdown("**2. Dürüst Akademik Metrikler (Held-Out Gold Benchmark)**")
        st.markdown("""
        | Görev | Metrik | Değer |
        | :--- | :--- | :--- |
        | **NLU Kategori Sınıflandırma** | Macro F1 | **%73.2** (Precision: %87.1) |
        | **NLU Niyet Sınıflandırma** | Macro F1 | **%88.0** (Precision: %88.9) |
        | **2026 Hibrit RAG Getirme** | Doc Hit@3 / MRR@3 | **%100.0 / 1.000** |
        | **Uçtan Uca Çıkarım Süresi** | Intel i5 CPU | **< 1.8 saniye (0 TL maliyet)** |
        """)
    st.caption("Teknik rapor PDF çıktısı: `docs/EsnafDoktor_Teknik_Rapor.pdf` dosyasındadır.")
