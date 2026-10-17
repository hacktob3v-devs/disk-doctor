# Kişi 2 · LLM — Detaylı Rehber

> Önce [00_ortak.md](00_ortak.md) dosyasını oku (5 dk).
> **Rolün:** Gemma 4'ü dükkân laptopunda (Ollama ile, internetsiz) çalıştırıp iki iş yaptırıyorsun:
> 1. Müşteri şikâyetinden **ön teşhis kartı** (JSON),
> 2. Disk sonucundan müşteriye **sade Türkçe rapor**.
>
> Ayrıca Super User'dan gerçek vakaları bulup Gemma'ya örnek olarak veren **mini-RAG** ve jürinin asıl sorusu için **ölçülmüş süreler** senin işin.
> **Kimseyi beklemiyorsun:** Her şeyi terminalden test edersin. Disk tarafı gerekiyorsa `core.mocks` içindeki sahte diski kullanırsın.

---

## 0. Teslim edeceklerin (özet)

| Saat | Teslim | Kime yarar |
|---|---|---|
| 19:45 | Gemma çalışıyor, ilk süre ölçümü | Herkes (kill rule) |
| 21:30 | `core/config.py`, `core/llm.py`, `core/triage.py` (önce benzer vaka olmadan) | Kişi 3 |
| 23:30 | `prompts/superuser_cases.jsonl` + `core/retrieval.py` → triage'a bağlı | Kişi 3 |
| 01:30 | `core/report.py` → `customer_report(...)` | Kişi 3 |
| 03:30 | `docs/timings.md` + yazının **"Why open beats a closed API"** bölümü | Kişi 3 (yazı) |

İmzalar (`core/contracts.py`):

```python
triage.triage(complaint: str) -> Triage
report.customer_report(shop: str, disk: DiskInfo, risk: Risk, triage: Triage | None) -> str   # Markdown
llm.warmup() -> bool          # arayüz açılışta bir kez çağırır
config.MODEL                  # arayüz kenar çubuğunda gösterir
```

---

## 1. 19:00–19:45 · Ollama ve Gemma (ilk 5 dakikada indirmeyi başlat!)

1. https://ollama.com/download → Windows → kur. Kurulunca Ollama arka planda çalışır (sistem tepsisinde lama simgesi).
2. https://ollama.com/library adresinde **gemma4** sayfasına bak; etiketleri (boyutları) gör.
3. Laptopa göre seç:
   - 8 GB RAM → en küçük varyant
   - 16 GB RAM → küçük/orta varyant
   - GPU yoksa küçük olan **her zaman** daha iyi. Demo hızı, kaliteden daha önemli.
4. İndir:

```powershell
ollama pull gemma4:<etiket>
ollama list
```

5. İlk test (süreyi kronometreyle ölç):

```powershell
ollama run gemma4:<etiket> "Bilgisayar açılıyor, fan dönüyor ama ekranda görüntü yok. Olası 3 sebebi Türkçe ve kısa yaz."
```

**Karar (19:45 SYNC 1'de söyle):** Cevap 20 saniyenin altındaysa bu model kalır. Değilse daha küçük varyanta geç.
Gemma 4 indirilemezse **B planı:** bir önceki nesil küçük Gemma. Yazıda hangi model kullanıldıysa o yazılır.

> **Demo laptopu senin laptopun değilse:** aynı `ollama pull` komutu demo laptopunda da **gece yarısından önce** çalıştırılmalı.

### Super User verisi (indirme beklerken, 10 dk)

1. https://data.stackexchange.com/superuser → **Compose Query** (kayıt gerekmez).
2. Şu sorguyu yapıştır → **Run Query** → sonuç altındaki **Download CSV**:

```sql
SELECT TOP 2000 q.Id, q.Title, q.Body, q.Score, a.Body AS AcceptedAnswer
FROM Posts q
JOIN Posts a ON a.Id = q.AcceptedAnswerId
WHERE q.PostTypeId = 1
  AND q.Score >= 3
  AND EXISTS (
    SELECT 1 FROM PostTags pt JOIN Tags t ON t.Id = pt.TagId
    WHERE pt.PostId = q.Id
      AND t.TagName IN ('hard-drive','ssd','motherboard','graphics-card','memory',
                        'power-supply','overheating','boot','display','laptop','bsod',
                        'hardware-failure','battery','fan')
  )
ORDER BY q.Score DESC
```

3. Dosyayı `data/superuser.csv` olarak kaydet.

> Sorgu hata verirse ya da az sonuç gelirse etiket adlarını sitede kontrol et (superuser.com/tags). `PostTags` tablosu yoksa `q.Tags LIKE '%hard-drive%' OR ...` biçimine geç.

---

## 2. 19:45–21:30 · Temel katman

### `core/config.py`

```python
"""Tek yerden model ayarı. Ortam değişkeniyle değiştirilebilir:  $env:DD_MODEL="gemma4:<etiket>" """
import os

MODEL = os.getenv("DD_MODEL", "gemma4")        # ollama list çıktısındaki tam adı yaz
KEEP_ALIVE = os.getenv("DD_KEEP_ALIVE", "2h")  # model belleğe yüklü kalsın, demo hızlı olsun
FAST_QUERY = os.getenv("DD_FAST_QUERY", "0") == "1"   # 1: arama ifadesi için LLM çağırma
```

> `"gemma4"` yerine **kendi seçtiğin tam etiketi** varsayılan yap. Herkes aynı modeli kullanmış olur.

### `core/llm.py`

```python
"""Ollama sarmalayıcı: JSON şemalı ve düz metin çağrılar, süre ölçümü, ısıtma."""
import json
import time

import ollama

from core.config import KEEP_ALIVE, MODEL


class LLMError(RuntimeError):
    pass


def _chat(system: str, user: str, fmt=None, temperature: float = 0.2):
    try:
        return ollama.chat(
            model=MODEL,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            format=fmt,
            keep_alive=KEEP_ALIVE,
            options={"temperature": temperature},
        )
    except Exception as e:
        raise LLMError(f"Ollama'ya ulaşılamadı ya da '{MODEL}' modeli yok: {e}") from e


def chat_json(system: str, user: str, schema: dict, retries: int = 1) -> tuple[dict, float]:
    """Şemaya uyan JSON döndürür. (veri, saniye)"""
    t0 = time.perf_counter()
    last = None
    for _ in range(retries + 1):
        r = _chat(system, user, fmt=schema)
        try:
            return json.loads(r["message"]["content"]), time.perf_counter() - t0
        except json.JSONDecodeError as e:
            last = e
    raise LLMError(f"Model geçerli JSON üretmedi: {last}")


def chat_text(system: str, user: str, temperature: float = 0.3) -> tuple[str, float]:
    t0 = time.perf_counter()
    r = _chat(system, user, temperature=temperature)
    return r["message"]["content"].strip(), time.perf_counter() - t0


def warmup() -> bool:
    """Modeli belleğe yükler; ilk gerçek çağrı hızlı olur."""
    try:
        ollama.generate(model=MODEL, prompt="ok", keep_alive=KEEP_ALIVE,
                        options={"num_predict": 1})
        return True
    except Exception:
        return False
```

Test:

```powershell
python -c "from core import llm; print(llm.warmup()); print(llm.chat_json('Sadece JSON ver.', 'Türkiye nin başkenti?', {'type':'object','properties':{'cevap':{'type':'string'}},'required':['cevap']}))"
```

### `prompts/triage_system.txt`

```text
Sen deneyimli bir bilgisayar tamircisinin yanında çalışan yardımcı teknisyensin.
Görevin: müşterinin Türkçe şikâyetinden ustaya hızlı bir ÖN TEŞHİS çıkarmak.

Kurallar:
- Sadece verilen şikâyete ve benzer vakalara dayan. Emin değilsen olasılığı "dusuk" yaz.
- En fazla 3 olası parça yaz, en olasıdan başla. Parça adları Türkçe ve kısa olsun
  (ör. "Ekran kartı", "RAM", "Güç kaynağı", "Disk", "Anakart", "Ekran paneli", "Batarya",
  "Soğutma / fan", "İşletim sistemi").
- "neden": o parçayı neden düşündüğünü tek cümleyle yaz.
- "kontrol_adimlari": ustanın dükkânda yapacağı 3-5 somut kontrol; ucuz ve hızlı olandan
  pahalı ve uzun olana doğru sırala.
- "ek_sorular": müşteriye sorulacak 2-3 kısa soru.
- "aciliyet": veri kaybı ya da donanım hasarı riski varsa "yuksek", yoksa "orta" veya "dusuk".
- "veri_riski": disk/depolama belirtisi varsa (tık sesi, donma, aşırı yavaşlama, açılmama,
  dosya kaybı, mavi ekran) true, yoksa false.
- Cevabın tamamı Türkçe olsun. Benzer vakalar İngilizce olabilir; onlardan sadece fikir al.
```

### `core/triage.py`

```python
"""Müşteri şikâyeti -> ön teşhis kartı (Gemma, yerel, JSON şema)."""
import time
from pathlib import Path

from core.contracts import Triage
from core.llm import chat_json

SYSTEM = Path("prompts/triage_system.txt").read_text(encoding="utf-8")
LIKELIHOOD = ("yuksek", "orta", "dusuk")
URGENCY = ("dusuk", "orta", "yuksek")

SCHEMA = {
    "type": "object",
    "required": ["olasi_parcalar", "kontrol_adimlari", "ek_sorular", "aciliyet", "veri_riski"],
    "properties": {
        "olasi_parcalar": {"type": "array", "items": {
            "type": "object", "required": ["parca", "olasilik", "neden"],
            "properties": {"parca": {"type": "string"},
                           "olasilik": {"type": "string", "enum": list(LIKELIHOOD)},
                           "neden": {"type": "string"}}}},
        "kontrol_adimlari": {"type": "array", "items": {"type": "string"}},
        "ek_sorular": {"type": "array", "items": {"type": "string"}},
        "aciliyet": {"type": "string", "enum": list(URGENCY)},
        "veri_riski": {"type": "boolean"},
    },
}


def _similar(complaint: str) -> list[dict]:
    try:
        from core.retrieval import similar_cases
        return similar_cases(complaint, k=3)
    except Exception as e:  # vaka dosyası henüz yoksa da çalışsın
        print(f"[triage] benzer vaka bulunamadı: {e}")
        return []


def _format_cases(cases: list[dict]) -> str:
    if not cases:
        return "(yok)"
    return "\n".join(f"- {c['title']}\n  Soru: {c['question'][:300]}\n  Kabul edilen cevap: {c['answer'][:400]}"
                     for c in cases)


def _normalize(d: dict) -> dict:
    parts = []
    for p in d.get("olasi_parcalar", [])[:3]:
        if isinstance(p, dict) and p.get("parca"):
            parts.append({"parca": str(p["parca"]),
                          "olasilik": p.get("olasilik") if p.get("olasilik") in LIKELIHOOD else "dusuk",
                          "neden": str(p.get("neden", ""))})
    return {
        "olasi_parcalar": parts,
        "kontrol_adimlari": [str(x) for x in d.get("kontrol_adimlari", [])][:5],
        "ek_sorular": [str(x) for x in d.get("ek_sorular", [])][:3],
        "aciliyet": d.get("aciliyet") if d.get("aciliyet") in URGENCY else "orta",
        "veri_riski": bool(d.get("veri_riski", False)),
    }


def triage(complaint: str) -> Triage:
    t0 = time.perf_counter()
    cases = _similar(complaint)
    user = (f"MÜŞTERİ ŞİKÂYETİ:\n{complaint.strip()}\n\n"
            f"BENZER GERÇEK VAKALAR (Super User, İngilizce):\n{_format_cases(cases)}")
    data, _ = chat_json(SYSTEM, user, SCHEMA)
    result = _normalize(data)
    result["benzer_vakalar"] = [{"title": c["title"], "url": c["url"]} for c in cases]
    result["sure_sn"] = round(time.perf_counter() - t0, 1)
    return result
```

Test (benzer vaka dosyası olmadan da çalışır):

```powershell
python -c "from core.triage import triage; import json; print(json.dumps(triage('Bilgisayar açılıyor, fanlar dönüyor ama ekrana görüntü gelmiyor.'), ensure_ascii=False, indent=2))"
```

**21:30 commit:**

```powershell
git pull --rebase
git add core/config.py core/llm.py core/triage.py prompts/triage_system.txt
git commit -m "Local Gemma via Ollama: JSON-schema triage"
git push
```

Kişi 3'e haber ver: **"triage hazır; config.MODEL ve llm.warmup() var."**

---

## 3. 21:30–23:30 · Mini-RAG (Super User benzer vakaları)

**Neden?** Küçük modele 30 örneklik uzun bir prompt vermek yavaş ve dağınık. Şikâyete en çok benzeyen **3 gerçek vakayı** bulup vermek hem hızlı hem daha isabetli. Arayüzde de kaynak linki olarak gösteriyoruz; bu jüriye güven verir.

### `scripts/prepare_superuser.py`

```python
"""SEDE CSV'sini temizleyip prompts/superuser_cases.jsonl üretir (CC BY-SA 4.0, link korunur).

Kullanım:  python -m scripts.prepare_superuser data/superuser.csv
"""
import csv
import json
import re
import sys

from bs4 import BeautifulSoup

SRC = sys.argv[1] if len(sys.argv) > 1 else "data/superuser.csv"
OUT = "prompts/superuser_cases.jsonl"
csv.field_size_limit(2**31 - 1)


def clean(html: str, limit: int) -> str:
    text = BeautifulSoup(html or "", "html.parser").get_text(" ")
    return re.sub(r"\s+", " ", text).strip()[:limit]


def main() -> None:
    n = 0
    with open(SRC, encoding="utf-8-sig", newline="") as f, open(OUT, "w", encoding="utf-8") as out:
        for row in csv.DictReader(f):
            q, a = clean(row["Body"], 800), clean(row["AcceptedAnswer"], 800)
            if len(q) < 40 or len(a) < 40:
                continue
            out.write(json.dumps({
                "id": int(row["Id"]),
                "title": row["Title"].strip(),
                "url": f"https://superuser.com/q/{row['Id']}",
                "question": q,
                "answer": a,
                "score": int(row["Score"]),
            }, ensure_ascii=False) + "\n")
            n += 1
    print(f"{n} vaka yazıldı: {OUT}")


if __name__ == "__main__":
    main()
```

```powershell
python -m scripts.prepare_superuser data/superuser.csv
```

> Bu dosya küçük (~1–2 MB) ve CC BY-SA lisanslı; `prompts/` altında **commit'lenir**. Ham CSV `data/` altında kalır.

### `core/retrieval.py`

```python
"""Şikâyete en benzer Super User vakalarını bulur (TF-IDF, tamamen yerel)."""
import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from core.config import FAST_QUERY

CASES_PATH = Path("prompts/superuser_cases.jsonl")

# LLM çağrısı başarısız olursa ya da FAST_QUERY=1 ise kullanılan basit sözlük
TR_EN = {
    "görüntü": "no display", "ekran": "screen display", "açılmıyor": "won't boot",
    "açılmaz": "won't turn on", "fan": "fan", "ısın": "overheating", "sıcak": "overheating",
    "mavi ekran": "bsod blue screen", "yavaş": "slow", "tık": "clicking noise hard drive",
    "ses": "noise", "disk": "hard drive", "şarj": "battery not charging", "batarya": "battery",
    "kapanıyor": "shuts down randomly", "donuyor": "freezes", "bip": "beep codes",
    "ram": "ram memory", "bellek": "memory", "klavye": "keyboard", "güç": "power supply",
    "kendi kendine": "restarts randomly", "siyah ekran": "black screen", "wifi": "wifi",
}
QUERY_SCHEMA = {"type": "object", "properties": {"query": {"type": "string"}},
                "required": ["query"]}

_cases: list[dict] | None = None
_vec = None
_mat = None


def _load() -> None:
    global _cases, _vec, _mat
    if _cases is not None:
        return
    _cases = [json.loads(line) for line in CASES_PATH.read_text(encoding="utf-8").splitlines() if line]
    _vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    _mat = _vec.fit_transform(f"{c['title']} {c['title']} {c['question']}" for c in _cases)


def keyword_query(complaint: str) -> str:
    low = complaint.lower()
    return " ".join(en for tr, en in TR_EN.items() if tr in low) or "computer hardware problem"


def to_query(complaint: str) -> str:
    kw = keyword_query(complaint)
    if FAST_QUERY:
        return kw
    try:
        from core.llm import chat_json
        data, _ = chat_json(
            "Translate the user's computer problem into a short English search query "
            "(max 12 words, symptoms only). Return JSON.", complaint, QUERY_SCHEMA)
        return f"{data['query']} {kw}"
    except Exception:
        return kw


def similar_cases(complaint: str, k: int = 3) -> list[dict]:
    _load()
    q = _vec.transform([to_query(complaint)])
    sims = linear_kernel(q, _mat).ravel()
    best = sims.argsort()[::-1][:k]
    return [_cases[i] for i in best if sims[i] > 0.05]
```

Test:

```powershell
python -c "from core.retrieval import similar_cases, to_query; c='Laptop çok yavaşladı, diskten tık tık ses geliyor'; print(to_query(c)); [print('-', x['title'], x['url']) for x in similar_cases(c)]"
```

Sonuçlar alakasızsa:
- `TR_EN` sözlüğüne kelime ekle.
- `min_df=1` dene.
- Arama ifadesi LLM'den saçma geliyorsa `$env:DD_FAST_QUERY="1"` ile sadece sözlüğü kullan (hem de 1 LLM çağrısı tasarruf edersin).

**23:30 CP1 commit:**

```powershell
git pull --rebase
git add core/retrieval.py scripts/prepare_superuser.py prompts/superuser_cases.jsonl
git commit -m "Mini-RAG over Super User cases (TF-IDF, local)"
git push
```

---

## 4. 23:30–01:30 · Müşteri raporu

**Altın kural:** Sayıları **model değil kod** yazar. Başlık satırındaki risk yüzdesi, disk modeli ve tarih Python ile üretilir. Gemma sadece açıklama metnini yazar. Böylece model hiçbir sayıyı uyduramaz.

### `prompts/report_system.txt`

```text
Sen bir bilgisayar tamircisi adına müşteriye kısa bir disk sağlık raporu yazıyorsun.
Okuyucu teknik bilgisi olmayan biri.

Kurallar:
- SADECE verilen bilgileri kullan. Yeni sayı, yüzde, tarih, marka ya da fiyat UYDURMA.
- Teknik terim kullanırsan hemen ardından parantez içinde basitçe açıkla.
- Korkutma ama net ol. Durum "Riskli" ise verilerin HEMEN yedeklenmesini ve diskin
  değiştirilmesini öner. "Dikkat" ise yakın zamanda yedek ve kontrol öner.
  "İyi durumda" ise düzenli yedeklemeyi hatırlat.
- Başlık yazma (ayrıca ekleniyor). Tam olarak şu üç bölümü Markdown ile yaz:
  ## Diskinizin durumu
  ## Bu ne anlama geliyor?
  ## Önerimiz
- "Önerimiz" bölümü 2-4 madde olsun. Toplam 150 kelimeyi geçme. Türkçe yaz.
```

### `core/report.py`

```python
"""Disk sonucundan müşteriye sade Türkçe rapor (Markdown)."""
import datetime
from pathlib import Path
from typing import Optional

from core.contracts import DiskInfo, Risk, Triage
from core.llm import LLMError, chat_text

SYSTEM = Path("prompts/report_system.txt").read_text(encoding="utf-8")
LEVEL_TR = {"green": "İyi durumda", "yellow": "Dikkat", "red": "Riskli"}
METHOD_TR = {"tabpfn": "TabPFN (gerçek disk arıza verisiyle)",
             "rf": "RandomForest (gerçek disk arıza verisiyle)",
             "nvme_rules": "NVMe sağlık kuralları"}


def _facts(shop: str, disk: DiskInfo, risk: Risk, triage: Optional[Triage]) -> str:
    lines = [
        f"DÜKKÂN: {shop}",
        f"DİSK: {disk['model']}, {'NVMe SSD' if disk['kind'] == 'nvme' else 'SATA/ATA disk'}, "
        f"{disk['capacity_gb']:.0f} GB, {disk['power_on_hours']} saat çalışmış",
        f"DURUM: {LEVEL_TR[risk['level']]} (arıza riski %{risk['risk'] * 100:.0f}, yöntem: {METHOD_TR[risk['method']]})",
        "BULGULAR:",
        *[f"- {d}" for d in risk["drivers"]],
    ]
    if triage and triage.get("olasi_parcalar"):
        lines.append("MÜŞTERİ ŞİKÂYETİNE GÖRE ÖN TEŞHİS: "
                     + ", ".join(p["parca"] for p in triage["olasi_parcalar"]))
    return "\n".join(lines)


def _fallback(risk: Risk) -> str:
    advice = {
        "red": "- Verilerinizi **hemen** yedekleyin.\n- Diskin en kısa sürede değiştirilmesini öneririz.",
        "yellow": "- Verilerinizi bu hafta içinde yedekleyin.\n- Diski birkaç hafta sonra tekrar kontrol ettirin.",
        "green": "- Düzenli yedekleme yapmaya devam edin.",
    }[risk["level"]]
    return (f"## Diskinizin durumu\n{LEVEL_TR[risk['level']]}.\n\n"
            "## Bu ne anlama geliyor?\n" + "\n".join(f"- {d}" for d in risk["drivers"])
            + f"\n\n## Önerimiz\n{advice}")


def customer_report(shop: str, disk: DiskInfo, risk: Risk, triage: Optional[Triage] = None) -> str:
    today = datetime.date.today().strftime("%d.%m.%Y")
    header = (f"# {shop} — Disk Sağlık Raporu\n\n"
              f"**Tarih:** {today} · **Disk:** {disk['model']} ({disk['capacity_gb']:.0f} GB) · "
              f"**Durum:** {LEVEL_TR[risk['level']]} · **Arıza riski:** %{risk['risk'] * 100:.0f}\n\n")
    try:
        body, _ = chat_text(SYSTEM, _facts(shop, disk, risk, triage))
    except LLMError:
        body = _fallback(risk)
    footer = ("\n\n---\n_Bu rapor bir ön değerlendirmedir; kesin teşhis için ustanızın kontrolü esastır. "
              "Rapor dükkândaki bilgisayarda, internete bağlanmadan hazırlanmıştır._")
    return header + body.strip() + footer
```

Test (disk tarafı için mock kullanılır; Kişi 1'i beklemezsin):

```powershell
python -c "from core import mocks, report; d=mocks.parse({}); r=mocks.predict(d); print(report.customer_report('Örnek Bilgisayar', d, r))"
```

Kontrol et:
- [ ] Gemma'nın metninde **başlıktakinden farklı bir sayı** var mı? Varsa prompt'u sıkılaştır.
- [ ] 150 kelimeyi aşıyor mu?
- [ ] Teknik terimler açıklanmış mı?

**01:30 öncesi commit:**

```powershell
git pull --rebase
git add core/report.py prompts/report_system.txt
git commit -m "Customer report: facts from code, wording from local Gemma"
git push
```

Kişi 3'e haber ver: **"report hazır, USE_MOCKS=0 ile deneyebilirsin."**

---

## 5. 01:30–03:30 · "Neden açık?" kanıtı: süre ölçümü

Jürinin asıl sorusu: *"Açık yaklaşım burada neden kapalı bir API'den daha iyi çalıştı?"* Bu soruya iddiayla değil, **ölçümle** cevap veriyoruz.

### `scripts/bench_llm.py`

```python
"""Yerel Gemma ile ön teşhis ve rapor sürelerini ölçer, docs/timings.md yazar.

Kullanım (Wi-Fi KAPALIYKEN çalıştır):  python -m scripts.bench_llm
"""
import platform
import statistics
import time
from pathlib import Path

from core import llm, mocks, report, triage
from core.config import MODEL

COMPLAINTS = [
    "Bilgisayar açılıyor, fanlar dönüyor ama ekrana görüntü gelmiyor.",
    "Laptop son haftalarda çok yavaşladı, diskten tık tık ses geliyor, bazen donuyor.",
    "Oyun oynarken 10 dakika sonra kendi kendine kapanıyor, alttan çok ısınıyor.",
]


def main() -> None:
    t0 = time.perf_counter()
    llm.warmup()
    cold = time.perf_counter() - t0

    tri = [triage.triage(c)["sure_sn"] for c in COMPLAINTS for _ in range(2)]

    disk = mocks.parse({})
    risk = mocks.predict(disk)
    rep = []
    for _ in range(3):
        t = time.perf_counter()
        report.customer_report("Test", disk, risk)
        rep.append(time.perf_counter() - t)

    text = f"""# Yerel çalışma süreleri

- Model: `{MODEL}` (Ollama, yerel)
- Makine: {platform.processor() or platform.machine()} · {platform.system()} {platform.release()}
- Ağ: **Wi-Fi kapalı**

| İşlem | Ortalama | En kötü |
|---|---|---|
| Modeli belleğe yükleme (ilk açılış, bir kez) | {cold:.1f} sn | — |
| Ön teşhis (benzer vaka arama dahil) | {statistics.mean(tri):.1f} sn | {max(tri):.1f} sn |
| Müşteri raporu | {statistics.mean(rep):.1f} sn | {max(rep):.1f} sn |

Rapor başına değişken maliyet: **0 TL**. Müşteri verisi bilgisayardan çıkmadı.
"""
    Path("docs/timings.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
```

```powershell
# Wi-Fi'ı kapat, sonra:
python -m scripts.bench_llm
```

Makine bilgisini elle düzelt (ör. "Lenovo ThinkPad, i5-1135G7, 16 GB RAM, GPU yok").

### "Why open beats a closed API here" (İngilizce taslak — kendi sayılarınla güncelle)

> The obvious way to build this is to send the complaint to a big hosted model. For a neighborhood repair shop, that's the wrong trade:
>
> - **Cost that scales with customers.** Every triage and every report would be a paid API call. With local Gemma, the marginal cost per customer is **zero**. The shop pays for the laptop it already owns.
> - **Customer data stays in the shop.** Serial numbers, what's on the disk, what the customer said: none of it leaves the machine.
> - **The internet is the least reliable part of a small shop.** We turned Wi-Fi off during the demo. Triage took **X s**, the report **Y s** on a **[laptop]**.
> - **No lock-in.** Model weights live on the disk. If a vendor changes prices or deprecates a model, the shop's tool doesn't change.
> - **The core isn't a chatbot anyway.** The risk number comes from TabPFN trained on real drive failures, a job a general chat API can't do from a S.M.A.R.T. table.

**03:30 commit:**

```powershell
git pull --rebase
git add scripts/bench_llm.py docs/timings.md
git commit -m "Measure local latency (offline)"
git push
```

---

## 6. 03:30–04:30 · COULD: sesli şikâyet (sadece CP3 yeşilse)

Sadece her şey çalışıyorsa ve Kişi 3 onaylarsa:

```powershell
pip install faster-whisper
```

`core/stt.py` → `transcribe(wav_bytes) -> str` (model: `small`, `language="tr"`, `device="cpu"`, `compute_type="int8"`).
Arayüz tarafında `st.audio_input` ile kayıt alınır (Kişi 3).
**Kural:** 04:30'da çalışmıyorsa tamamen çıkarılır. Çekirdeği asla riske atma.

---

## 7. 04:30–05:15 · Demo provası (sen sürüyorsun)

- [ ] Demo laptopunda `ollama list` ile model var mı?
- [ ] Wi-Fi kapalı → `streamlit run app.py` → 3 örnek şikâyet → 3 disk → rapor. **2 kez.**
- [ ] Kronometreyle süre tut; 3 dakikayı geçmesin.
- [ ] Demo başlamadan 2 dakika önce uygulamayı aç (warmup çalışsın).
- [ ] Laptop prizde, uyku modu kapalı, bildirimler kapalı.

---

## 8. Jüride senin cevaplayacağın sorular

| Soru | Cevabın |
|---|---|
| Neden kapalı API değil? | Ezber cümle + `docs/timings.md` sayıları + "az önce Wi-Fi kapalıydı" |
| Super User İngilizce, kullanıcı Türkçe? | Şikâyeti kısa bir İngilizce arama ifadesine çeviriyoruz, benzer vakaları buluyoruz, Gemma Türkçe cevap veriyor |
| Yanlış teşhis koyarsa? | Ustanın yerine geçmiyor; olasılık, kontrol sırası ve kaynak vakaları gösteriyor |
| Model sayı uyduruyor mu? | Hayır: rapordaki tüm sayılar koddan geliyor, Gemma sadece açıklama metnini yazıyor |
| Neden Gemma? | Open-weight, laptopta çalışacak boyutları var, Türkçesi yeterli, Ollama ile tek komutla kuruluyor |

**Ezber cümle:** *"A neighborhood repair shop can't pay per-request API fees, often has bad internet, and shouldn't ship customer data to a third party — so DiskDoctor runs entirely on the shop's own laptop. We just turned Wi-Fi off, and it still works."*

---

## Hızlı sorun giderme

| Belirti | Çözüm |
|---|---|
| `LLMError: Ollama'ya ulaşılamadı` | Sistem tepsisinde Ollama çalışıyor mu? `ollama serve` |
| `model not found` | `ollama list` ile tam adı al → `$env:DD_MODEL="gemma4:<etiket>"` |
| İlk çağrı 60+ sn | Normal (model yükleniyor). `warmup()` + `keep_alive` bunu demo öncesine taşır |
| JSON'da alan eksik | `_normalize` doldurur; sürekli eksikse prompt'a örnek çıktı ekle |
| Türkçe bozuk | `temperature` 0.2'ye indir; prompt'a "Türkçe yaz" vurgusu |
| Benzer vakalar alakasız | `DD_FAST_QUERY=1`, sözlüğe kelime ekle, `min_df=1` |
| `FileNotFoundError: prompts/...` | Komutu repo kökünden çalıştır |
