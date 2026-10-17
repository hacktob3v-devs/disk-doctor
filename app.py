"""DiskDoctor — Streamlit arayüzü.  Çalıştır:  streamlit run app.py"""
import datetime
import html
import json
import os
import socket
import time
from pathlib import Path

import markdown
import streamlit as st

USE_MOCKS = os.getenv("USE_MOCKS", "1") == "1"

if USE_MOCKS:
    from core import mocks as triage_mod, mocks as parser_mod, mocks as disk_mod
    from core import mocks as nvme_mod, mocks as report_mod, mocks as llm_mod
    MODEL_NAME = "mock"
else:
    from core import triage as triage_mod          # Kişi 2
    from core import report as report_mod          # Kişi 2
    from core import llm as llm_mod                # Kişi 2
    from core import smart_parser as parser_mod    # Kişi 1
    from core import disk_model as disk_mod        # Kişi 1
    from core import nvme_rules as nvme_mod        # Kişi 1
    from core.config import MODEL as MODEL_NAME

DEMO_DIR = Path("demo")
EXAMPLES = [
    ("Görüntü yok", "Bilgisayar açılıyor, fanlar dönüyor ama ekrana görüntü gelmiyor."),
    ("Tık sesi + yavaşlık", "Laptop son haftalarda çok yavaşladı, diskten tık tık ses geliyor, bazen donuyor."),
    ("Isınıp kapanıyor", "Oyun oynarken 10 dakika sonra kendi kendine kapanıyor, alttan çok ısınıyor."),
]
LEVEL = {"green": ("İyi durumda", "#2E7D32", "#E8F5E9"),
         "yellow": ("Dikkat", "#B26A00", "#FFF4E0"),
         "red": ("Riskli", "#C62828", "#FDECEA")}
LIKELIHOOD = {"yuksek": "🔴 yüksek", "orta": "🟠 orta", "dusuk": "🟢 düşük"}
URGENCY = {"yuksek": "🔴 Yüksek", "orta": "🟠 Orta", "dusuk": "🟢 Düşük"}
METHOD = {"tabpfn": "TabPFN · gerçek disk arıza verisi (Backblaze)",
          "rf": "RandomForest · gerçek disk arıza verisi (Backblaze)",
          "nvme_rules": "NVMe sağlık kuralları"}

st.set_page_config(page_title="DiskDoctor", page_icon="💽", layout="wide")
ss = st.session_state
for key, default in [("complaint", ""), ("shop", "Örnek Bilgisayar"), ("triage", None),
                     ("disk", None), ("risk", None), ("report", None), ("last_secs", None)]:
    ss.setdefault(key, default)


@st.cache_resource(show_spinner="Modeller yükleniyor (yerel)…")
def warm_up() -> None:
    llm_mod.warmup()
    try:
        disk_mod.load_model()
    except FileNotFoundError as e:
        st.warning(str(e))


@st.cache_data(ttl=15)
def is_online() -> bool:
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=1).close()
        return True
    except OSError:
        return False


def read_json(data: bytes) -> dict:
    # PowerShell 5.1 '>' ile kaydedilen dosyalar UTF-16 olur; ikisini de dene
    for enc in ("utf-8-sig", "utf-16"):
        try:
            return json.loads(data.decode(enc))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise ValueError("Bu dosya smartctl -j çıktısına benzemiyor.")


def assess(disk: dict) -> dict:
    return nvme_mod.score(disk) if disk["kind"] == "nvme" else disk_mod.predict(disk)


def report_html(md_text: str, shop: str) -> str:
    body = markdown.markdown(md_text)
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<title>{html.escape(shop)} — Disk raporu</title>
<style>body{{font-family:'Segoe UI',Arial,sans-serif;max-width:720px;margin:40px auto;
color:#222;line-height:1.55;padding:0 16px}}h1{{border-bottom:3px solid #E8603F;padding-bottom:6px}}
@media print{{body{{margin:0 auto}}}}</style></head><body>{body}</body></html>"""


def set_example(text: str) -> None:
    ss.complaint = text


warm_up()

st.title("💽 DiskDoctor")
st.caption("Mahalle tamircisi için ön teşhis ve disk sağlığı — tamamen bu bilgisayarda, internetsiz.")
tab_triage, tab_disk = st.tabs(["🩺 Ön Teşhis", "💽 Disk Sağlığı"])

# ---------------- Ön teşhis ----------------
with tab_triage:
    cols = st.columns(len(EXAMPLES))
    for col, (label, text) in zip(cols, EXAMPLES):
        col.button(label, on_click=set_example, args=(text,), width="stretch")
    st.text_area("Müşterinin şikâyeti", key="complaint", height=110,
                 placeholder="Müşteri ne diyor? Kendi cümleleriyle yazın…")
    if st.button("Ön teşhis koy", type="primary", disabled=not ss.complaint.strip()):
        with st.spinner("Gemma düşünüyor (yerel)…"):
            try:
                ss.triage = triage_mod.triage(ss.complaint)
                ss.last_secs = ss.triage.get("sure_sn")
            except Exception as e:
                st.error(f"Ön teşhis yapılamadı: {e}")

    t = ss.triage
    if t:
        st.divider()
        left, right = st.columns([3, 2], gap="large")
        with left:
            st.markdown(f"**Aciliyet:** {URGENCY.get(t['aciliyet'], t['aciliyet'])}")
            if t["veri_riski"]:
                st.warning("⚠️ Veri kaybı riski var — işlemden önce yedek alın, Disk Sağlığı sekmesine bakın.")
            st.markdown("#### Olası parçalar")
            for p in t["olasi_parcalar"]:
                st.markdown(f"- **{p['parca']}** · {LIKELIHOOD.get(p['olasilik'], p['olasilik'])} — {p['neden']}")
            st.markdown("#### Kontrol sırası")
            st.markdown("\n".join(f"{i}. {s}" for i, s in enumerate(t["kontrol_adimlari"], 1)))
        with right:
            st.markdown("#### Müşteriye sorulacaklar")
            st.markdown("\n".join(f"- {q}" for q in t["ek_sorular"]))
            if t["benzer_vakalar"]:
                st.markdown("#### Benzer gerçek vakalar")
                st.markdown("\n".join(f"- [{c['title']}]({c['url']})" for c in t["benzer_vakalar"]))
                st.caption("Kaynak: Super User · CC BY-SA 4.0")

# ---------------- Disk sağlığı ----------------
with tab_disk:
    c1, c2 = st.columns(2)
    uploaded = c1.file_uploader("smartctl -j -a çıktısı (.json)", type=["json"])
    demos = sorted(DEMO_DIR.glob("*.json"))
    choice = c2.selectbox("…ya da demo dosyası", ["—"] + [p.name for p in demos])
    with c2.expander("Kendi diskimi nasıl okurum?"):
        st.code('smartctl --scan\ncmd /c "smartctl -j -a /dev/sda > disk.json"', language="powershell")
        st.caption("PowerShell'i yönetici olarak açın.")

    source = None
    if uploaded is not None:
        source = uploaded.getvalue()
    elif choice != "—":
        source = (DEMO_DIR / choice).read_bytes()

    if st.button("Diski değerlendir", type="primary", disabled=source is None):
        try:
            t0 = time.perf_counter()
            ss.disk = parser_mod.parse(read_json(source))
            ss.risk = assess(ss.disk)
            ss.report = None
            ss.last_secs = time.perf_counter() - t0
        except Exception as e:
            ss.disk = ss.risk = None
            st.error(f"Disk okunamadı: {e}")

    d, r = ss.disk, ss.risk
    if d and r:
        label, fg, bg = LEVEL[r["level"]]
        st.markdown(
            f"<div style='background:{bg};border-left:10px solid {fg};padding:18px 24px;"
            f"border-radius:10px;margin:12px 0'>"
            f"<div style='font-size:16px;color:{fg};font-weight:600'>{label}</div>"
            f"<div style='font-size:48px;font-weight:800;color:{fg};line-height:1.1'>"
            f"%{r['risk'] * 100:.0f} arıza riski</div>"
            f"<div style='color:#555;margin-top:4px'>Yöntem: {METHOD.get(r['method'], r['method'])}</div>"
            f"</div>", unsafe_allow_html=True)
        a, b = st.columns(2, gap="large")
        with a:
            st.markdown("#### Etkili bulgular")
            st.markdown("\n".join(f"- {x}" for x in r["drivers"]))
        with b:
            st.markdown("#### Disk")
            st.markdown(
                f"- **Model:** {d['model']}\n"
                f"- **Tür:** {'NVMe SSD' if d['kind'] == 'nvme' else 'SATA / ATA'}\n"
                f"- **Kapasite:** {d['capacity_gb']:.0f} GB\n"
                f"- **Çalışma süresi:** {d['power_on_hours']:,} saat\n"
                f"- **Sıcaklık:** {d['temperature_c'] if d['temperature_c'] is not None else '—'} °C")

        st.divider()
        if st.button("📝 Müşteri raporu oluştur"):
            with st.spinner("Rapor yazılıyor (yerel)…"):
                try:
                    t0 = time.perf_counter()
                    ss.report = report_mod.customer_report(ss.shop, d, r, ss.triage)
                    ss.last_secs = time.perf_counter() - t0
                except Exception as e:
                    st.error(f"Rapor oluşturulamadı: {e}")
        if ss.report:
            with st.container(border=True):
                st.markdown(ss.report)
            st.download_button("⬇️ Raporu indir (yazdırılabilir)", report_html(ss.report, ss.shop),
                               file_name=f"disk-raporu-{datetime.date.today()}.html", mime="text/html")

# ---------------- Kenar çubuğu (en sonda: son süreyi göstersin) ----------------
with st.sidebar:
    st.header("Dükkân")
    st.text_input("Dükkân adı", key="shop")
    st.divider()
    if is_online():
        st.info("🌐 İnternet bağlı — ama hiçbir veri dışarı gönderilmiyor")
    else:
        st.success("✅ Çevrimdışı — her şey bu bilgisayarda")
    st.metric("Son işlem süresi", f"{ss.last_secs:.1f} sn" if ss.last_secs else "—")
    st.metric("API maliyeti", "0 TL")
    st.caption(f"Model: {MODEL_NAME} · yerel (Ollama)")
    if USE_MOCKS:
        st.warning("Mock modu açık (USE_MOCKS=1)")
