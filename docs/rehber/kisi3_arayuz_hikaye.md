# Kişi 3 · Arayüz ve Hikâye — Detaylı Rehber

> Önce [00_ortak.md](00_ortak.md) dosyasını oku (5 dk).
> **Rolün:** Jürinin gördüğü her şey sende: arayüz, tamirci hikâyesi, **en ağır kriter olan İngilizce yazı**, README, demo kaydı, MLH/DEV gönderimi ve sunum.
> **Kimseyi beklemiyorsun:** Arayüzü `core/mocks.py` ile baştan sona kurarsın. Kişi 1 ve Kişi 2 "hazır" dediğinde `USE_MOCKS=0` yaparsın; kodunu değiştirmen gerekmez.
> **Ortak dosyaların sahibi sensin:** `core/contracts.py`, `requirements.txt`, `README.md`. Başkaları bunlar için sana yazar.

---

## 0. Teslim edeceklerin (özet)

| Saat | Teslim |
|---|---|
| 19:30 | Tamirci telefon görüşmesi notları (`post/tamirci_notlari.md` — **commit'leme**, kişisel bilgi var) |
| 21:30 | Mock ile uçtan uca çalışan `app.py` |
| 23:30 | Yazı: **The person** + **The problem** bölümleri |
| 01:30 | `USE_MOCKS=0` ile uçtan uca çalışma + README kurulum + **MLH ilk gönderim** |
| 03:30 | Ekran görüntüleri + yazı: **What we built** |
| 04:30 | Demo GIF + yedek ekran kaydı |
| 05:15 | Yazı v1 DEV'de taslak + MLH gönderimi güncel |
| 05:30 | Sunum |

---

## 1. 19:00–19:30 · Tamirciyi ara (her şeyden önce!)

Yazının en ağır kriter olduğunu unutma: **gerçek bir kişi, gerçek bir rakam, gerçek bir cümle** bizi diğer takımlardan ayırır.

### Arama metni

> "Merhaba, ben Fırat Üniversitesi'nden [ad]. Şu an bir yarışmada, bilgisayar tamircilerinin işini kolaylaştıracak bir uygulama yapıyoruz. 5 dakikanızı alabilir miyim? Birkaç soru soracağım."

| # | Soru | Not al |
|---|---|---|
| 1 | Ayda kaç müşteri diski bozulmuş olarak, verisiyle birlikte getiriyor? | rakam |
| 2 | Disk değişimi + veri taşıma kaça? Veri kurtarma kaça? | TL |
| 3 | Müşteriye diskin durumunu şu an nasıl söylüyorsunuz? | yöntem |
| 4 | Dükkânda internet ne kadar güvenilir? Müşteri bilgisini başka bir şirkete göndermek sorun olur mu? | cevap |
| 5 | Diskin bozulacağını önceden söyleyen bir araç için tek seferlik ya da aylık ne verirdiniz? | TL |
| + | Aklında kalan bir müşteri hikâyesi var mı? (ör. kaybolan fotoğraflar) | **aynen** yaz |
| İzin | "Adınızı/dükkânınızın adını yazımızda kullanabilir miyiz?" | evet/hayır |

**Kurallar:**
- İzin yoksa yazıda "a repair shop owner in Elazığ" de.
- Rakam uydurma. Gelmezse "we asked; he estimated…" de.
- Pazar günü yüz yüze gidip uygulamayı kullandıracağını söyle ve saat al.

---

## 2. 19:30–21:30 · Arayüz (mock ile)

### 2.1 `requirements.txt` — `markdown` ekle (rapor indirme için)

```text
streamlit
ollama
tabpfn
scikit-learn
pandas
numpy
joblib
beautifulsoup4
markdown
```

```powershell
pip install markdown
```

### 2.2 `core/mocks.py` — NVMe ve `score` ekle

Mock'lar, gerçek modüllerle **aynı fonksiyon adlarına** sahip olmalı. Arayüz NVMe diskleri `nvme_rules.score`, diğerlerini `disk_model.predict` ile değerlendirecek; ayrıca `llm.warmup` ve `disk_model.load_model` çağrılacak.

```python
"""Gerçek modüllerle aynı imzalara sahip sahte fonksiyonlar.

Arayüz USE_MOCKS=1 iken bunları kullanır; böylece modeller hazır olmadan geliştirilebilir.
"""
import time
from typing import Optional

from core.contracts import DiskInfo, Risk, Triage, level_for

MODEL = "mock"


def warmup() -> bool:
    return True


def load_model():
    return None, "mock"


def triage(complaint: str) -> Triage:
    time.sleep(0.5)
    return {
        "olasi_parcalar": [
            {"parca": "Ekran kartı", "olasilik": "yuksek", "neden": "Fan dönüyor ama görüntü yok"},
            {"parca": "RAM", "olasilik": "orta", "neden": "POST aşamasında takılma olabilir"},
        ],
        "kontrol_adimlari": ["Harici monitör dene", "RAM'i çıkarıp tek modülle dene",
                             "Ekran kartını çıkarıp dahili grafikle dene"],
        "ek_sorular": ["Açılışta bip sesi var mı?", "Sorun ne zamandan beri var?"],
        "aciliyet": "orta",
        "veri_riski": False,
        "benzer_vakalar": [{"title": "PC turns on but no display", "url": "https://superuser.com/"}],
        "sure_sn": 0.5,
    }


def parse(smartctl_json: dict) -> DiskInfo:
    if "nvme_smart_health_information_log" in smartctl_json:
        return {"kind": "nvme", "model": "Mock NVMe 512GB", "serial": "MOCK-NVME",
                "capacity_gb": 512.0, "power_on_hours": 2300, "temperature_c": 41,
                "features": {"percentage_used": 7, "media_errors": 0}}
    return {"kind": "ata", "model": "WDC WD10EZEX", "serial": "MOCK-0001",
            "capacity_gb": 1000.0, "power_on_hours": 31000, "temperature_c": 38,
            "features": {"smart_5_raw": 112, "smart_197_raw": 24}}


def predict(disk: DiskInfo) -> Risk:
    risk = 0.82
    return {"risk": risk, "level": level_for(risk),
            "drivers": ["Bekleyen (okunamayan) sektör: 24", "Yeniden atanmış sektör: 112"],
            "method": "tabpfn"}


def score(disk: DiskInfo) -> Risk:
    return {"risk": 0.05, "level": "green",
            "drivers": ["Belirgin bir sorun yok (ömür kullanımı %7)"], "method": "nvme_rules"}


def customer_report(shop: str, disk: DiskInfo, risk: Risk, triage: Optional[Triage] = None) -> str:
    time.sleep(0.5)
    return (f"# {shop} — Disk Sağlık Raporu\n\n"
            f"**Disk:** {disk['model']} · **Arıza riski:** %{risk['risk'] * 100:.0f}\n\n"
            "## Diskinizin durumu\nDiskinizde arıza belirtileri var.\n\n"
            "## Önerimiz\n- Verilerinizi hemen yedekleyin.\n- Diskin değiştirilmesini öneririz.\n\n"
            "---\n_Bu rapor bir ön değerlendirmedir._")
```

### 2.3 `app.py` — tam sürüm

```python
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
```

> **Neden kenar çubuğu en sonda?** Streamlit sayfayı yukarıdan aşağı çalıştırır. Kenar çubuğu en sonda çizilince "Son işlem süresi" o anki işlemi gösterir. Dükkân adı `session_state` içinde tutulduğu için rapor bölümü onu sorunsuz okur.

Çalıştır:

```powershell
streamlit run app.py
```

Kontrol listesi (mock ile):
- [ ] Üç örnek butonu metin kutusunu dolduruyor
- [ ] Ön teşhis kartı görünüyor
- [ ] Demo dosyası seçince ve "Diski değerlendir" deyince kırmızı kart çıkıyor (`demo/` boşsa, Kişi 1'in rehberindeki NVMe örneğini `demo/my_nvme.json` olarak geçici kaydet)
- [ ] Rapor oluşuyor ve HTML indiriliyor; tarayıcıda açıp Ctrl+P ile PDF'e basılabiliyor
- [ ] Wi-Fi kapatınca kenar çubuğu 15 sn içinde "Çevrimdışı" oluyor

**21:30 commit:**

```powershell
git pull --rebase
git add app.py core/mocks.py requirements.txt
git commit -m "UI: triage and disk health tabs, printable report, offline indicator"
git push
```

---

## 3. 21:30–23:30 · Yazıya başla

### 3.1 Önce 10 dakika oku (20:00 civarı da olur)

Slayt 25'teki kazanan yazılar:
- `dev.to/iclaldogan/residues-a-terminal-game-inside-the-dying-mind-of-alan-turing-2p67`
- `dev.to/iclaldogan/echolalia-a-haunted-desktop-where-two-ai-voices-finish-writing-you-5hhk`

Dikkat et: nasıl açılıyorlar (sahne mi, özellik mi?), başlıklar, görsel sıklığı, paragraf uzunluğu.

### 3.2 `post/devto_draft.md` — iskelet ve ilk iki bölüm

```markdown
*This is a submission for the Hacktoberfest 2026 DEV Challenge, Week 2: Side Hustle.*

# The Repair Shop That Saw the Disk Dying First

## The person
<!-- Sahne ile aç. Tamircinin tezgâhı, açılmayan bir laptop, "Bütün fotoğraflarım bundaydı" diyen
bir müşteri. SADECE tamirciden duyduğun gerçek hikâyeyi kullan. -->

[Name / "A repair shop owner"] runs a small computer repair shop in Elazığ, Türkiye.
Every month, about [X] customers walk in with a laptop that won't boot — and a disk that has
already taken their photos, thesis or invoices with it. "[Real quote from the call]," he told us.

## The boring, repeated job
<!-- Her müşteride aynı sorular; diskin durumunu tahminle söylemek; veri kurtarma pahalı (kaç TL?). -->

## What we built
<!-- 2 özellik + GIF. Wi-Fi kapalı GIF'i burada. -->

## How it works
<!-- Diyagram + Kişi 1 ve Kişi 2'nin taslakları -->

## Why open beats a closed API here
<!-- Kişi 2'nin taslağı + docs/timings.md tablosu -->

## Our first user
<!-- Tamircinin tepkisi + "Would he pay?" + gece kullandırdığımız kişinin cümlesi -->

## Honest limitations
<!-- Kişi 1'in taslağı -->

## How we built it
<!-- GitHub Copilot kullanımı + DevRelay oturumu gömülü -->

## What's next
- Log the shop's own drives and refit the model on them
- Voice input for complaints
- Repair guides for the suspected part

## Team & links
- Team: @devuser1, @devuser2, @devuser3
- Repo: https://github.com/hacktob3v-devs/disk-doctor (MIT)

## Prize categories
Gemma · TabPFN · GitHub Copilot
```

> DEV'de yazıyı açarken **challenge submission template** kullanılmalı (`#devchallenge #hf26challenge` etiketleri otomatik gelir). Taslağı oraya yapıştırırsın.

### Yazım kuralları
- Her iddianın yanında kanıt olsun: ekran görüntüsü, süre, metrik.
- Paragraflar kısa olsun (en fazla 3–4 cümle).
- Toplam: 1 GIF, 1 diyagram, 2–4 ekran görüntüsü, 1 metrik tablosu, 1 süre tablosu.
- Abartı yok: "revolutionary", "AI-powered magic" gibi ifadeler kullanma.

---

## 4. 23:30–01:30 · Gerçek modüllere geçiş ve ilk gönderim

### 4.1 Geçiş

Kişi 1 ve Kişi 2 "hazır" dediğinde:

```powershell
git pull --rebase
python -m scripts.train_disk_model          # models/ git'te yok; demo laptopunda bir kez
$env:USE_MOCKS="0"
streamlit run app.py
```

Bir şey kırılırsa: hata mesajını **sahibine** gönder (dosya adı + satır). Kendin düzeltme. Bu sırada `USE_MOCKS=1` ile çalışmaya devam et.

### 4.2 README'yi tamamla

`README.md` içinde şunlar olsun:
- [ ] 3 cümlelik hikâye (yazının özeti)
- [ ] GIF (03:30 sonrası)
- [ ] Hızlı kurulum: `ollama pull`, `pip install`, `python -m scripts.prepare_backblaze`, `python -m scripts.train_disk_model`, `streamlit run app.py`, `$env:USE_MOCKS="0"`
- [ ] "Results": `docs/metrics.md` ve `docs/timings.md` linkleri
- [ ] Veri kaynakları ve lisanslar (zaten var)
- [ ] Limitations (Kişi 1'in metni)

### 4.3 MLH'ya ilk gönderim (01:30 — zorunlu)

1. Sunumdaki QR kodu / MLH etkinlik sayfası → **Challenges / Submit**.
2. Proje adı: **DiskDoctor**. Repo: `https://github.com/hacktob3v-devs/disk-doctor`.
3. Kısa açıklama (İngilizce):
   > *DiskDoctor helps a neighborhood computer repair shop triage customer complaints and spot hard drives that are about to fail, before the customer loses their data. It runs fully offline on the shop's laptop: Gemma 4 via Ollama for triage and customer reports, and TabPFN trained on Backblaze drive-failure data for risk scoring.*
4. Takım arkadaşlarını ekle. Kaydet.
5. Bu bir **ilk sürüm**; 05:15'te güncellenecek.

---

## 5. 01:30–04:30 · Görseller ve demo kaydı

### Ekran görüntüleri (`docs/screenshots/`)
- `triage.png` — ön teşhis kartı
- `disk_red.png` — kırmızı risk kartı (failing_hdd.json)
- `disk_green.png` — NVMe yeşil
- `report.png` — müşteri raporu
- `offline.png` — kenar çubuğunda "Çevrimdışı ✓"

Windows: `Win + Shift + S` → alan seç → yapıştırıp kaydet.

### Demo GIF ve yedek video
- **Video:** `Win + Alt + R` (Xbox Game Bar) ya da OBS. Tam 3 dakikalık demoyu **Wi-Fi kapalı** kaydet. Dosyayı demo laptopuna ve bir telefona koy.
- **GIF:** ScreenToGif (ücretsiz) ile 15–20 saniyelik iki GIF: (1) Wi-Fi kapatma + ön teşhis, (2) kırmızı disk + rapor.

**03:30 commit:**

```powershell
git pull --rebase
git add docs/screenshots/ README.md
git commit -m "README: screenshots, setup, results"
git push
```

---

## 6. 04:30–05:30 · Son hazırlık

- [ ] Yazı v1 → DEV'de **taslak** (submission template ile). Pazar günü tamircinin yüz yüze tepkisi eklenip **yayınlanacak**.
- [ ] MLH gönderimini güncelle: GIF, yazı taslağı linki.
- [ ] DevRelay oturumunu kaydet/paylaş (Copilot kanıtı); linki yazının "How we built it" bölümüne koy.
- [ ] Sunum provası ×2, kronometreyle.

---

## 7. Sunum metni (3 dk) — sen açıp kapatıyorsun

| Süre | Kim | Söylenecek / yapılacak |
|---|---|---|
| 0:00–0:20 | **Sen** | "Elazığ'da bir tamirci her ay [X] müşteriye aynı cümleyi kuruyor: 'Keşke diski daha önce getirseydin.' Disk öldüğünde veri de gidiyor. Biz ona diskin **ölmeden önce** haber veren bir asistan yaptık." |
| 0:20–0:30 | Kişi 2 | Wi-Fi'ı kapatır. "Bundan sonraki her şey internetsiz." Kenar çubuğunda "Çevrimdışı ✓". |
| 0:30–1:10 | Kişi 2 | Örnek şikâyet → ön teşhis kartı. "Gemma 4, bu laptopta çalışıyor. Benzer gerçek vakaları da gösteriyor." |
| 1:10–2:10 | Kişi 1 | Önce `my_nvme.json` (yeşil). Sonra `failing_hdd.json` (kırmızı). "Bu, Backblaze verisinde **ertesi gün gerçekten ölmüş** bir disk. TabPFN, bekleyen sektörlerden bunu yakaladı." |
| 2:10–2:40 | **Sen** | "Müşteri raporu oluştur" → indir. "Süre ekranda. API maliyeti: sıfır." |
| 2:40–3:00 | **Sen** | Tamircinin cümlesi + "ne verirdin?" cevabı. **"Open weights, open data, zero per-customer cost."** |

**Bir şey takılırsa:** 3 saniye bekleme, yedek videoya geç: "Canlı sistem burada; zamanı verimli kullanmak için kayda geçiyorum."

### Jüride senin cevaplayacağın sorular

| Soru | Cevabın |
|---|---|
| Para verirler mi? | Tamircinin gerçek cevabı + "erken yakalanan her disk = disk değişimi + yedekleme işi" |
| Kim kullanacak? | Tek kişilik/küçük bilgisayar tamir dükkânları; kurulum tek laptop |
| Lisanslar? | Kod MIT; Backblaze'e atıf; Super User CC BY-SA, her vakada link; ham veri repoda yok |
| Neden bu fikir? | Gerçek bir kişinin her hafta yaşadığı, parası net bir dert (slayt 13 ve 16) |

---

## 8. Pazar (tampon) ve Pazartesi 09:59 son teslim

- [ ] Tamirciye yüz yüze 10 dk kullandır; tepkisini ve "para verir miydin?" cevabını **aynen** yaz.
- [ ] Bir fotoğraf (izin alarak) → yazının "Our first user" bölümü.
- [ ] Yazıyı yayınla: İngilizce, submission template, tek post, takım DEV kullanıcı adları, kategoriler (Gemma, TabPFN, GitHub Copilot), DevRelay gömülü.
- [ ] MLH gönderimini son hâliyle güncelle.
- [ ] **19 Ekim Pazartesi 09:59'dan önce.** Son geceye bırakma.

---

## Hızlı sorun giderme

| Belirti | Çözüm |
|---|---|
| `streamlit` bulunamadı | venv aktif mi? `.venv\Scripts\Activate.ps1` |
| `Activate.ps1` çalışmıyor | `Set-ExecutionPolicy -Scope Process Bypass` |
| `ModuleNotFoundError: markdown` | `pip install markdown` |
| `USE_MOCKS=0` ile `ModuleNotFoundError: core.triage` | Kişi 2 henüz push etmemiş → `git pull --rebase` ya da mock'a dön |
| `FileNotFoundError: models/train_context.csv` | `python -m scripts.train_disk_model` (önce `data/drives_sample.csv` gerekli; Kişi 1'den dosyayı iste) |
| Ön teşhis çok yavaş | Kişi 2'ye söyle: `DD_FAST_QUERY=1` ya da daha küçük model |
| Sayfa her tıklamada sıfırlanıyor | Değeri `st.session_state` içinde tut (kodda zaten öyle) |
