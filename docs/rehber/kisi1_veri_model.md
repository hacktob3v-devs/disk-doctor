# Kişi 1 · Veri ve Model — Detaylı Rehber

> Önce [00_ortak.md](00_ortak.md) dosyasını oku (5 dk).
> **Rolün:** Diskin ölüp ölmeyeceğini tahmin eden kısmı sen kuruyorsun. Gerçek arıza verisi (Backblaze), TabPFN modeli, `smartctl` çıktısını okuma ve NVMe diskler için kural tabanlı skor senin işin.
> **Kimseyi beklemiyorsun:** Her şeyi terminalden test edersin. Arayüz şu an mock kullanıyor; senin modülün hazır olunca Kişi 3 `USE_MOCKS=0` yapar ve arayüz otomatik olarak senin kodunu kullanır.

---

## 0. Teslim edeceklerin (özet)

| Saat | Teslim | Kime yarar |
|---|---|---|
| 21:30 | `data/drives_sample.csv` (yerelde) | Sana |
| 23:30 | `core/disk_model.py` → `predict(disk)` çalışıyor + `docs/metrics.md` | Kişi 3 (arayüz), yazı |
| 23:30 | `core/smart_parser.py` → `parse(json)` (ATA) | Kişi 3 |
| 01:30 | `core/nvme_rules.py` → `score(disk)` + NVMe parse + `demo/*.json` (3 dosya) | Kişi 3 (demo) |
| 03:30 | Yazının **"How it works (model)"** ve **"Honest limitations"** bölümleri | Kişi 3 (yazı) |

Fonksiyon imzaları `core/contracts.py` içinde. **Döndürdüğün sözlük birebir o şekilde olmalı.**

```python
smart_parser.parse(smartctl_json: dict) -> DiskInfo
disk_model.predict(disk: DiskInfo) -> Risk          # kind == "ata"
nvme_rules.score(disk: DiskInfo) -> Risk            # kind == "nvme"
disk_model.load_model() -> (clf, kind)              # arayüz açılışta bir kez çağırır
```

---

## 1. 19:00–19:30 · İndirmeleri başlat (ilk 5 dakikada!)

### 1.1 Backblaze verisi (en uzun süren iş)

1. Tarayıcıda **https://www.backblaze.com/cloud-storage/resources/hard-drive-test-data** (ya da backblaze.com/drivestats → "Download the data") sayfasını aç.
2. **En son yayınlanmış çeyreğin** zip dosyasını indir (ör. `data_Q2_2026.zip`). Boyutu ~1 GB veya daha fazla olabilir.
3. İndirme sürerken kurulumlara devam et.
4. Bittiğinde aç:

```powershell
mkdir data\backblaze_raw
Expand-Archive -Path $HOME\Downloads\data_Q2_2026.zip -DestinationPath data\backblaze_raw
```

> Klasörde `2026-04-01.csv` gibi her gün için bir CSV olmalı. Alt klasör ya da `__MACOSX` klasörü olabilir; script bunları kendisi halleder.

**Wi-Fi çok yavaşsa:** telefon hotspot'u dene. 21:00'de hâlâ inmemişse kill rule devreye girer: önce parser + NVMe (bölüm 5–6) üzerinde çalış, veri gelince modele dön.

### 1.2 Paketler ve smartmontools

```powershell
pip install -r requirements.txt
```

**smartmontools (Windows):**
1. https://www.smartmontools.org → Download → Windows installer (`smartmontools-*.win32-setup.exe`).
2. Kur; kurulumda "Add to PATH" seçeneğini işaretle.
3. **Yönetici olarak** yeni bir PowerShell aç (Başlat → PowerShell → sağ tık → Yönetici olarak çalıştır):

```powershell
smartctl --scan
```

Çıktı örnekleri: `/dev/sda -d ata` (SATA disk) veya `/dev/nvme0 -d nvme` (NVMe SSD).

### 1.3 TabPFN duman testi (19:30'da bitmiş olmalı)

```powershell
python -c "from sklearn.datasets import load_iris; from tabpfn import TabPFNClassifier; X,y=load_iris(return_X_y=True); c=TabPFNClassifier(device='cpu').fit(X,y); print('TabPFN OK', c.predict(X[:3]))"
```

- İlk çalıştırmada model ağırlıkları indirilir (birkaç dakika sürebilir).
- **Hata mesajında "gated", "license", "token" ya da "Hugging Face" geçiyorsa:** hata mesajındaki model sayfasına git, lisansı kabul et, sonra terminalde `huggingface-cli login` yazıp kendi token'ını gir.
- **20:30'a kadar hâlâ çalışmıyorsa:** RandomForest ile devam et (`$env:DD_DISK_MODEL="rf"`). Kod buna hazır. 03:30'da TabPFN'i tekrar dene.
- **Yapma:** `tabpfn-client` (bulut sürümü) kullanma. "Tamamen yerel" iddiamız bozulur.

---

## 2. 19:45–21:30 · Backblaze örneklemi

### Neden böyle örnekliyoruz?

- **Disk başına tek satır.** Aynı diskin farklı günleri hem eğitim hem test setine düşerse model ezberler ve metrik yalan söyler. Buna veri sızıntısı (leakage) denir. Jüride veri bilimciler var; bunu soracaklar.
- **Arızalı diskler:** `failure == 1` olan satır, yani diskin çalıştığı son gün.
- **Sağlıklı diskler:** çeyreğe yayılmış ~8 günden, hiç arızalanmamış disklerden rastgele birer satır.
- **Dengeli ve küçük:** TabPFN küçük tablolarda çok iyi çalışır ve CPU'da hızlı kalır.

### `scripts/prepare_backblaze.py`

```python
"""Backblaze çeyrek verisinden disk başına 1 satırlık örneklem üretir.

Kullanım (repo kökünden):
    python -m scripts.prepare_backblaze data/backblaze_raw
"""
import glob
import os
import sys

import pandas as pd

RAW = sys.argv[1] if len(sys.argv) > 1 else "data/backblaze_raw"
OUT = "data/drives_sample.csv"
SMART = ["smart_5_raw", "smart_9_raw", "smart_187_raw", "smart_188_raw",
         "smart_194_raw", "smart_197_raw", "smart_198_raw"]
COLS = ["date", "serial_number", "model", "capacity_bytes", "failure"] + SMART
HEALTHY_DAYS = 8
HEALTHY_N = 3000


def read_day(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=lambda c: c in COLS, low_memory=False)
    return df.reindex(columns=COLS)   # bazı günlerde eksik sütun olursa NaN ile doldurur


def main() -> None:
    files = sorted(f for f in glob.glob(os.path.join(RAW, "**", "*.csv"), recursive=True)
                   if "__MACOSX" not in f)
    if not files:
        sys.exit(f"CSV bulunamadı: {RAW}")
    print(f"{len(files)} günlük dosya bulundu")

    fails = []
    for i, f in enumerate(files, 1):
        d = read_day(f)
        fails.append(d[d.failure == 1])
        if i % 10 == 0:
            print(f"  {i}/{len(files)} gün tarandı")
    fails = pd.concat(fails).drop_duplicates("serial_number", keep="last")
    print(f"Arızalı disk: {len(fails)}")

    step = max(1, len(files) // HEALTHY_DAYS)
    pool = pd.concat(read_day(f) for f in files[::step])
    pool = pool[(pool.failure == 0) & (~pool.serial_number.isin(fails.serial_number))]
    healthy = pool.groupby("serial_number").sample(1, random_state=42)
    healthy = healthy.sample(min(HEALTHY_N, len(healthy)), random_state=42)
    print(f"Sağlıklı disk: {len(healthy)}")

    df = pd.concat([fails, healthy], ignore_index=True)
    # S.M.A.R.T. değerlerinin hiçbiri olmayan satırlar (bazı SSD'ler) işe yaramaz
    df = df.dropna(subset=["smart_5_raw", "smart_187_raw", "smart_197_raw"], how="all")
    df[SMART] = df[SMART].fillna(0)
    df.to_csv(OUT, index=False)
    print(f"Yazıldı: {OUT} ({len(df)} satır, {int(df.failure.sum())} arızalı)")


if __name__ == "__main__":
    main()
```

Çalıştır:

```powershell
python -m scripts.prepare_backblaze data/backblaze_raw
```

Süre: 90 günlük dosya için birkaç dakika. Beklerken bölüm 5'e (parser) başla.

**Kontrol:**

```powershell
python -c "import pandas as pd; d=pd.read_csv('data/drives_sample.csv'); print(d.shape); print(d.failure.value_counts()); print(d.describe().T[['mean','max']])"
```

Beklenen: birkaç yüz ile birkaç bin arası arızalı disk ve ~3000 sağlıklı disk.

---

## 3. 21:30–23:30 · Model: `core/disk_model.py`

### Tasarım kararları

- **Öznitelikler:** 5 kritik sayaç (log1p ile), her biri için `>0` bayrağı, sıcaklık ve çalışma saati (log).
- **Model kaydı:** TabPFN'in "eğitimi" aslında bağlam (context) tablosunu saklamaktır. O yüzden pickle yerine **bağlam tablosunu** `models/train_context.csv` olarak kaydediyoruz ve uygulama açılırken `fit` ediyoruz. Bu birkaç saniye sürer ve sürüm uyumsuzluğu riski yoktur.
- **Yedek:** TabPFN yüklenemezse otomatik olarak RandomForest kullanılır. `method` alanı hangisinin kullanıldığını söyler; yazıda dürüstçe o yazılır.

### `core/disk_model.py`

```python
"""Disk arıza riski: Backblaze verisiyle TabPFN (yedek: RandomForest)."""
import os

import numpy as np
import pandas as pd

from core.contracts import DiskInfo, Risk, level_for

CONTEXT_PATH = "models/train_context.csv"

CRITICAL = {
    "smart_5_raw": "Yeniden atanmış sektör",
    "smart_187_raw": "Düzeltilemeyen hata",
    "smart_188_raw": "Komut zaman aşımı",
    "smart_197_raw": "Bekleyen (okunamayan) sektör",
    "smart_198_raw": "Çevrimdışı düzeltilemeyen sektör",
}
FEATURES = (list(CRITICAL)
            + ["has_" + c.split("_")[1] for c in CRITICAL]
            + ["temp_c", "log_hours"])

_clf = None
_kind = None


def _col(df: pd.DataFrame, name: str) -> pd.Series:
    if name in df:
        return pd.to_numeric(df[name], errors="coerce")
    return pd.Series(np.nan, index=df.index)


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for c in CRITICAL:
        v = _col(df, c).fillna(0).clip(lower=0)
        out[c] = np.log1p(v)
        out["has_" + c.split("_")[1]] = (v > 0).astype(int)
    t = _col(df, "smart_194_raw")
    out["temp_c"] = t.where((t > 0) & (t < 100)).fillna(40)
    out["log_hours"] = np.log1p(_col(df, "smart_9_raw").fillna(0).clip(lower=0))
    return out[FEATURES]


def new_classifier():
    if os.getenv("DD_DISK_MODEL", "tabpfn") == "tabpfn":
        try:
            from tabpfn import TabPFNClassifier
            return TabPFNClassifier(device="cpu"), "tabpfn"
        except Exception as e:  # kurulum / import sorunu
            print(f"[disk_model] TabPFN yok, RandomForest kullanılıyor: {e}")
    from sklearn.ensemble import RandomForestClassifier
    return RandomForestClassifier(n_estimators=300, class_weight="balanced",
                                  min_samples_leaf=3, random_state=42), "rf"


def fit_on(ctx: pd.DataFrame):
    clf, kind = new_classifier()
    X, y = make_features(ctx), ctx["failure"].astype(int)
    try:
        clf.fit(X, y)
    except Exception as e:  # ör. ağırlık indirilemedi
        if kind != "tabpfn":
            raise
        print(f"[disk_model] TabPFN fit başarısız, RandomForest: {e}")
        os.environ["DD_DISK_MODEL"] = "rf"
        clf, kind = new_classifier()
        clf.fit(X, y)
    return clf, kind


def load_model():
    global _clf, _kind
    if _clf is None:
        if not os.path.exists(CONTEXT_PATH):
            raise FileNotFoundError(
                f"{CONTEXT_PATH} yok. Önce: python -m scripts.train_disk_model")
        _clf, _kind = fit_on(pd.read_csv(CONTEXT_PATH))
    return _clf, _kind


def drivers_for(features: dict) -> list[str]:
    out = []
    for c, label in CRITICAL.items():
        v = features.get(c) or 0
        if v > 0:
            out.append(f"{label}: {int(v)}")
    hours = features.get("smart_9_raw") or 0
    if hours > 40000:
        out.append(f"Uzun çalışma süresi: {int(hours):,} saat")
    return out or ["Kritik S.M.A.R.T. değerlerinde sorun görünmüyor"]


def predict(disk: DiskInfo) -> Risk:
    clf, kind = load_model()
    row = pd.DataFrame([disk["features"]])
    risk = float(clf.predict_proba(make_features(row))[0, 1])
    return {"risk": round(risk, 3), "level": level_for(risk),
            "drivers": drivers_for(disk["features"]), "method": kind}
```

### `scripts/train_disk_model.py` — eğit, değerlendir, kaydet

```python
"""Bağlam setini seçer, test setinde dürüst metrik hesaplar, docs/metrics.md yazar.

Kullanım:  python -m scripts.train_disk_model
"""
import os

import pandas as pd
from sklearn.metrics import (confusion_matrix, precision_score, recall_score,
                             roc_auc_score)
from sklearn.model_selection import GroupShuffleSplit

from core.disk_model import CONTEXT_PATH, fit_on, make_features

N_PER_CLASS = 480     # toplam ~960 satır: TabPFN CPU'da hızlı kalır


def main() -> None:
    df = pd.read_csv("data/drives_sample.csv")
    tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
                  .split(df, groups=df["serial_number"]))
    train, test = df.iloc[tr], df.iloc[te]

    pos, neg = train[train.failure == 1], train[train.failure == 0]
    ctx = pd.concat([pos.sample(min(N_PER_CLASS, len(pos)), random_state=42),
                     neg.sample(min(N_PER_CLASS, len(neg)), random_state=42)])

    clf, kind = fit_on(ctx)
    p = clf.predict_proba(make_features(test))[:, 1]
    y = test["failure"].astype(int)
    pred = (p >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred).ravel()

    os.makedirs("models", exist_ok=True)
    ctx.to_csv(CONTEXT_PATH, index=False)

    report = f"""# Disk modeli — test sonuçları

- Model: **{kind}**
- Veri: Backblaze Drive Stats, tek çeyrek, disk başına 1 satır
- Ayrım: `serial_number` bazında (aynı disk hem eğitimde hem testte yok)
- Bağlam (eğitim) seti: {len(ctx)} satır ({int(ctx.failure.sum())} arızalı)
- Test seti: {len(test)} satır ({int(y.sum())} arızalı, {int((y == 0).sum())} sağlıklı)

| Metrik | Değer |
|---|---|
| Recall (arızalıyı yakalama) | {recall_score(y, pred):.2f} |
| Precision | {precision_score(y, pred, zero_division=0):.2f} |
| ROC-AUC | {roc_auc_score(y, p):.2f} |

Confusion matrix (eşik 0.5):

|  | Tahmin: sağlıklı | Tahmin: arızalı |
|---|---|---|
| **Gerçek: sağlıklı** | {tn} | {fp} |
| **Gerçek: arızalı** | {fn} | {tp} |

**Dikkat:** Test setindeki arızalı oranı gerçek hayattakinden çok daha yüksek (dengeli örneklem).
Gerçek kullanımda precision daha düşük olur. Arızalı disklerin bir kısmı bütün S.M.A.R.T.
değerleri sıfırken ölür; bu disklerin hiçbir modelle yakalanması mümkün değildir.
"""
    os.makedirs("docs", exist_ok=True)
    with open("docs/metrics.md", "w", encoding="utf-8") as f:
        f.write(report)
    print(report)


if __name__ == "__main__":
    main()
```

Çalıştır:

```powershell
python -m scripts.train_disk_model
```

TabPFN, CPU'da birkaç yüz test satırını tahmin ederken 1–3 dakika sürebilir; normal.

**Hata: "more than 1000 samples on CPU"** → `N_PER_CLASS` değerini 400'e indir.

### Tek başına test (arayüz gerekmez)

```powershell
python -c "from core import disk_model as m; d={'kind':'ata','model':'x','serial':'x','capacity_gb':1000,'power_on_hours':30000,'temperature_c':38,'features':{'smart_5_raw':120,'smart_197_raw':24,'smart_9_raw':30000}}; print(m.predict(d))"
python -c "from core import disk_model as m; d={'kind':'ata','model':'x','serial':'x','capacity_gb':1000,'power_on_hours':8000,'temperature_c':35,'features':{'smart_9_raw':8000}}; print(m.predict(d))"
```

Beklenen: ilki `red` ya da `yellow`, ikincisi `green`. Ters çıkıyorsa öznitelik hesabına bak.

**23:30 CP1 sonrası commit:**

```powershell
git pull --rebase
git add scripts/prepare_backblaze.py scripts/train_disk_model.py core/disk_model.py docs/metrics.md
git commit -m "Disk model: Backblaze sampling, TabPFN with RF fallback, test metrics"
git push
```

---

## 4. Metrikler hakkında dürüstlük (jüri için çok önemli)

- Recall'ı **olduğu gibi** söyle. %100 çıkmaz; çıkarsa bir yerde sızıntı var demektir.
- ROC-AUC 0.95'in üzerinde çıkarsa da şüphelen: aynı seri numarası iki tarafta mı? `fillna(0)` bazı modelleri ayırt edici mi yapıyor?
- `docs/metrics.md` dosyası README'ye ve yazıya **aynen** girer.

---

## 5. 23:30–01:30 · `core/smart_parser.py`

`smartctl -j -a` çıktısını `DiskInfo` şekline çevirir. Hem SATA/ATA hem NVMe disklerle çalışır.

```python
"""smartctl -j -a çıktısını DiskInfo'ya çevirir (ATA ve NVMe)."""
from core.contracts import DiskInfo

ATA_IDS = (5, 9, 187, 188, 194, 197, 198)


def parse(j: dict) -> DiskInfo:
    if not isinstance(j, dict) or "device" not in j:
        raise ValueError("Bu dosya smartctl -j çıktısı değil (device alanı yok).")
    dev = j.get("device", {})
    kind = "nvme" if (dev.get("type") == "nvme"
                      or "nvme_smart_health_information_log" in j) else "ata"
    capacity = j.get("user_capacity", {}).get("bytes") or j.get("nvme_total_capacity") or 0
    info: DiskInfo = {
        "kind": kind,
        "model": j.get("model_name") or j.get("model_family") or "Bilinmeyen disk",
        "serial": j.get("serial_number", "?"),
        "capacity_gb": round(capacity / 1e9, 1),
        "power_on_hours": int(j.get("power_on_time", {}).get("hours", 0) or 0),
        "temperature_c": j.get("temperature", {}).get("current"),
        "features": {},
    }

    if kind == "nvme":
        log = j.get("nvme_smart_health_information_log", {})
        info["features"] = dict(log)
        if not info["power_on_hours"]:
            info["power_on_hours"] = int(log.get("power_on_hours", 0))
        if info["temperature_c"] is None:
            info["temperature_c"] = log.get("temperature")
        return info

    table = j.get("ata_smart_attributes", {}).get("table", [])
    if not table:
        raise ValueError("ATA S.M.A.R.T. tablosu yok. Komut 'smartctl -j -a' ile mi alındı?")
    raw = {a["id"]: (a.get("raw", {}) or {}).get("value", 0) for a in table}
    feats = {f"smart_{i}_raw": int(raw.get(i, 0) or 0) for i in ATA_IDS}
    # Bazı üreticiler 9 ve 194'ün ham değerini paketli yazar; smartctl'in çözdüğü değeri kullan
    if info["power_on_hours"]:
        feats["smart_9_raw"] = info["power_on_hours"]
    if info["temperature_c"] is not None:
        feats["smart_194_raw"] = info["temperature_c"]
    info["features"] = feats
    return info
```

### Kendi diskini oku (yönetici PowerShell)

PowerShell 5.1'de `>` yönlendirmesi dosyayı **UTF-16** olarak yazar. Arayüz bunu da okuyabiliyor, ama en temizi `cmd` ile UTF-8 yazmak:

```powershell
smartctl --scan
cmd /c "smartctl -j -a /dev/sda > demo\my_disk.json"
# NVMe ise:
cmd /c "smartctl -j -a /dev/nvme0 > demo\my_nvme.json"
```

Test:

```powershell
python -c "import json; from core.smart_parser import parse; print(parse(json.load(open('demo/my_nvme.json', encoding='utf-8'))))"
```

> **Gizlilik:** Kendi diskinin seri numarası dosyada yer alır. Commit'lemeden önce `serial_number` alanını `DEMO-NVME-001` gibi bir değerle değiştir.

---

## 6. `core/nvme_rules.py` — NVMe için kural tabanlı skor

**Neden gerekli?** Demo laptoplarının çoğunda NVMe SSD var. NVMe disklerde Backblaze'in kullandığı `smart_5`, `smart_197` gibi öznitelikler **yok**; bu yüzden TabPFN modeli NVMe diske uygulanamaz. NVMe kendi sağlık günlüğünü (health log) tutar; biz de onu basit, açıklanabilir kurallarla puanlıyoruz.

```python
"""NVMe sağlık günlüğünden kural tabanlı risk skoru."""
from core.contracts import DiskInfo, Risk, level_for


def score(disk: DiskInfo) -> Risk:
    n = disk["features"]
    risk, drivers = 0.05, []

    cw = n.get("critical_warning", 0) or 0
    if cw:
        risk = max(risk, 0.90)
        drivers.append(f"Diskin kendi kritik uyarı bayrağı açık (kod {cw})")

    media = n.get("media_errors", 0) or 0
    if media:
        risk = max(risk, 0.75)
        drivers.append(f"Medya / veri bütünlüğü hatası: {media}")

    spare = n.get("available_spare", 100)
    thr = n.get("available_spare_threshold", 10)
    if spare <= thr:
        risk = max(risk, 0.85)
        drivers.append(f"Yedek alan eşiğin altında: %{spare} (eşik %{thr})")
    elif spare < 50:
        risk = max(risk, 0.45)
        drivers.append(f"Yedek alan azalmış: %{spare}")

    used = n.get("percentage_used", 0) or 0
    if used >= 100:
        risk = max(risk, 0.70)
        drivers.append(f"Üreticinin öngördüğü yazma ömrü aşıldı: %{used}")
    elif used >= 80:
        risk = max(risk, 0.50)
        drivers.append(f"Yazma ömrünün çoğu kullanılmış: %{used}")

    temp = disk.get("temperature_c")
    if temp and temp >= 70:
        risk = max(risk, 0.35)
        drivers.append(f"Yüksek sıcaklık: {temp} °C")

    if not drivers:
        risk = max(risk, used / 400)
        drivers = [f"Belirgin bir sorun yok (ömür kullanımı %{used})"]

    return {"risk": round(risk, 2), "level": level_for(risk),
            "drivers": drivers, "method": "nvme_rules"}
```

Test:

```powershell
python -c "from core.nvme_rules import score; print(score({'kind':'nvme','temperature_c':40,'features':{'critical_warning':0,'media_errors':0,'available_spare':100,'available_spare_threshold':10,'percentage_used':7}}))"
python -c "from core.nvme_rules import score; print(score({'kind':'nvme','temperature_c':40,'features':{'critical_warning':0,'media_errors':3,'available_spare':8,'available_spare_threshold':10,'percentage_used':91}}))"
```

---

## 7. `scripts/make_demo_json.py` — demo dosyaları (01:30'a kadar)

Demoda 3 dosya kullanacağız:

| Dosya | İçerik | Beklenen sonuç |
|---|---|---|
| `demo/healthy_hdd.json` | Backblaze'den gerçek, sağlıklı bir disk | Yeşil |
| `demo/failing_hdd.json` | Backblaze'den **bir sonraki gün gerçekten ölmüş** bir disk | Kırmızı |
| `demo/my_nvme.json` | Kendi laptopumuzun NVMe'si (seri no maskeli) | Yeşil |

```python
"""Backblaze satırlarından smartctl -j biçiminde demo dosyaları üretir.

Kullanım:  python -m scripts.make_demo_json
"""
import json

import pandas as pd

from core import disk_model

NAMES = {5: "Reallocated_Sector_Ct", 9: "Power_On_Hours", 187: "Reported_Uncorrect",
         188: "Command_Timeout", 194: "Temperature_Celsius", 197: "Current_Pending_Sector",
         198: "Offline_Uncorrectable"}


def to_smartctl(row: pd.Series, serial: str) -> dict:
    table = [{"id": i, "name": n, "raw": {"value": int(row.get(f"smart_{i}_raw", 0) or 0)}}
             for i, n in NAMES.items()]
    return {
        "_source": f"Generated from a Backblaze Drive Stats row ({row['date']}), "
                   f"not a live smartctl read. failure={int(row['failure'])}",
        "device": {"name": "/dev/sda", "type": "sat"},
        "model_name": str(row["model"]),
        "serial_number": serial,
        "user_capacity": {"bytes": int(row["capacity_bytes"])},
        "power_on_time": {"hours": int(row["smart_9_raw"])},
        "temperature": {"current": int(row["smart_194_raw"])},
        "ata_smart_attributes": {"table": table},
    }


def main() -> None:
    df = pd.read_csv("data/drives_sample.csv")
    ctx = set(pd.read_csv(disk_model.CONTEXT_PATH)["serial_number"])
    df = df[~df.serial_number.isin(ctx)]          # modelin hiç görmediği diskler

    failing = df[(df.failure == 1) & (df.smart_197_raw > 0) & (df.smart_5_raw > 0)]
    failing = failing.sort_values("smart_197_raw", ascending=False).iloc[0]
    healthy = df[(df.failure == 0) & (df.smart_5_raw == 0) & (df.smart_197_raw == 0)]
    healthy = healthy[healthy.model == failing.model]
    healthy = (healthy if len(healthy) else df[df.failure == 0]).iloc[0]

    for name, row in [("failing_hdd", failing), ("healthy_hdd", healthy)]:
        data = to_smartctl(row, serial=f"DEMO-{name.upper()}")
        with open(f"demo/{name}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(name, row["model"], {c: int(row[c]) for c in row.index if c.startswith("smart_")})


if __name__ == "__main__":
    main()
```

Çalıştır ve doğrula:

```powershell
python -m scripts.make_demo_json
python -c "import json; from core.smart_parser import parse; from core.disk_model import predict; [print(f, predict(parse(json.load(open(f'demo/{f}.json'))))) for f in ['healthy_hdd','failing_hdd']]"
```

Arızalı disk kırmızı çıkmazsa başka bir arızalı satır seç (ör. `.iloc[1]`). Ama **jüriye bunu söyleme fırsatı da var:** "Model her arızayı yakalamıyor; işte metrikler."

**NVMe laptop yoksa** (demo laptopunda SATA disk varsa) `demo/my_nvme.json` için şu örneği kullan ve README'de "örnek" olduğunu belirt:

```json
{
  "_source": "Sample NVMe health log for demo purposes",
  "device": {"name": "/dev/nvme0", "type": "nvme"},
  "model_name": "Sample NVMe SSD 512GB",
  "serial_number": "DEMO-NVME-001",
  "nvme_total_capacity": 512110190592,
  "power_on_time": {"hours": 2310},
  "temperature": {"current": 41},
  "nvme_smart_health_information_log": {
    "critical_warning": 0, "temperature": 41, "available_spare": 100,
    "available_spare_threshold": 10, "percentage_used": 7, "media_errors": 0,
    "num_err_log_entries": 0, "power_on_hours": 2310, "unsafe_shutdowns": 38
  }
}
```

**01:30 CP2 öncesi commit:**

```powershell
git pull --rebase
git add core/smart_parser.py core/nvme_rules.py scripts/make_demo_json.py demo/healthy_hdd.json demo/failing_hdd.json demo/my_nvme.json
git commit -m "smartctl parser (ATA + NVMe), NVMe rules, demo disk files"
git push
```

Sonra Kişi 3'e haber ver: **"Modüllerim hazır, USE_MOCKS=0 yapabilirsin. Önce `python -m scripts.train_disk_model` çalıştırılmış olmalı."**

> Demo laptopu senin bilgisayarın değilse: `data/` ve `models/` git'te yok. Demo laptopunda da `prepare_backblaze` + `train_disk_model` çalıştırılmalı **ya da** `models/train_context.csv` dosyasını USB/Discord ile kopyala (sadece ~100 KB).

---

## 8. 01:30–03:30 · Yazı ve görseller

### Ekran görüntüleri
- `docs/metrics.md` tablosunun ekran görüntüsü → `docs/screenshots/metrics.png`
- Kırmızı risk kartı (Kişi 3'ten iste ya da arayüzden al)

### "How it works — the disk model" (İngilizce taslak, kendi sayılarınla güncelle)

> We trained on **Backblaze Drive Stats**, a public dataset where a cloud storage company logs the S.M.A.R.T. counters of its drives every day, and marks the last day before a drive dies. We took one quarter, kept **one row per drive** (the last day for drives that failed, a random day for drives that didn't), and split train and test **by serial number**, so the model never sees the same physical drive twice.
>
> The classifier is **TabPFN**, a foundation model for small tables: no hyperparameter tuning, a few seconds to "fit" on ~1,000 rows, and it runs on the shop's laptop CPU. On the held-out drives it catches **X%** of the drives that failed (recall) with an ROC-AUC of **Y**.
>
> NVMe drives don't report the same counters, so for them we use a transparent rule set on the NVMe health log (critical warning, media errors, spare capacity, wear).

### "Honest limitations" (İngilizce taslak)

> - **Data-center drives are not laptop drives.** Backblaze drives are mostly HDDs running 24/7 in racks. The warning signs (reallocated and pending sectors) are the same physics, but the exact probabilities won't transfer one-to-one.
> - **Balanced test set.** Real failure rates are a fraction of a percent per year; in real use, precision will be lower than our table suggests.
> - **Some drives die silently.** A part of the failed drives had all-zero counters the day before. No model catches those.
> - **NVMe uses rules, not a learned model.**
> - **It's a second opinion, not a verdict.** The technician decides.
> - **Next step:** log the shop's own drives and outcomes, and refit on that.

---

## 9. 03:30–04:30 · Kenar durum testleri

Hepsini dene; hiçbiri uygulamayı **çökertmemeli**. Hata varsa anlaşılır bir mesaj vermeli.

- [ ] Boş JSON `{}` → `ValueError("...smartctl -j çıktısı değil...")`
- [ ] `smartctl -j -i` çıktısı (S.M.A.R.T. tablosu yok) → anlaşılır hata
- [ ] USB kutusundaki disk (`device.type == "sat"`) → ATA yolu
- [ ] Değerleri eksik NVMe log → varsayılanlarla çalışıyor
- [ ] UTF-16 kaydedilmiş dosya (arayüz bunu çözüyor; `parse` dict alır)

**04:30 sonrası:** Başka bir takımdan birine 2 dakika kullandır. Söylediği tek cümleyi aynen not al ve Kişi 3'e ver.

---

## 10. Jüride senin cevaplayacağın sorular

| Soru | Cevabın |
|---|---|
| Backblaze veri merkezi verisi; laptopa genellenir mi? | Sınırlılık olarak kabul ediyoruz. Yeniden atanmış ve bekleyen sektör sinyalleri disk tipinden bağımsız olarak anlamlı. NVMe için ayrı kural yolu var. Sonraki adım dükkânın kendi verisi. |
| Metrikler? | `docs/metrics.md` tablosundaki sayılar. Disk bazında ayrım, sızıntı yok. Dengeli örneklem olduğu için gerçek dünyada precision daha düşük olur. |
| Neden TabPFN? | Küçük tablo verisinde ayar gerektirmeden güçlü; saniyeler içinde kuruluyor; dükkânın verisi geldikçe yeni satır eklemek yeterli. |
| Neden XGBoost değil? | Denedik/denemedik — dürüst ol. TabPFN'in avantajı sıfır ayar ve küçük veride iyi kalibrasyon. RF yedeğimiz var. |
| Arızalı disk demo verisi gerçek mi? | Evet, Backblaze'de bir sonraki gün ölmüş gerçek bir diskin değerleri; dosyanın `_source` alanında yazıyor. |

---

## Hızlı sorun giderme

| Belirti | Çözüm |
|---|---|
| `ModuleNotFoundError: core` | Komutu repo kökünden ve `python -m scripts.xxx` biçiminde çalıştır |
| `MemoryError` prepare sırasında | `HEALTHY_DAYS = 4` yap |
| TabPFN çok yavaş | `N_PER_CLASS = 300` |
| `smartctl` "Permission denied" | PowerShell'i **yönetici olarak** aç |
| `smartctl` diski görmüyor | `smartctl --scan-open`; USB kutularında `-d sat` ekle |
| JSON okunamıyor | Dosya UTF-16 olabilir: `cmd /c "smartctl ... > dosya.json"` ile tekrar al |
