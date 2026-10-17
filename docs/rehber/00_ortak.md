# 00 · Ortak kurallar (herkes önce bunu okusun, 5 dakika)

Üç kişi **aynı anda, birbirini beklemeden** çalışıyor. Bu dosya, paralel çalışmayı mümkün kılan kuralları içerir.
Kişisel rehberler:

- [Kişi 1 — Veri ve Model](kisi1_veri_model.md)
- [Kişi 2 — LLM](kisi2_llm.md)
- [Kişi 3 — Arayüz ve Hikâye](kisi3_arayuz_hikaye.md)

---

## 1. Paralel çalışmanın 4 kuralı

1. **Herkes sadece kendi dosyalarına yazar.** Böylece merge çatışması çıkmaz.
2. **Ortak dil `core/contracts.py`.** Her modül oradaki şekli (TypedDict) döndürür. Değiştirmek gerekirse önce sync toplantısında konuşulur ve dosyayı sadece Kişi 3 değiştirir.
3. **Kimse kimseyi beklemez.**
   - Kişi 3 arayüzü `core/mocks.py` ile geliştirir (`USE_MOCKS=1`).
   - Kişi 1 ve Kişi 2 kendi modüllerini **terminalden** test eder; arayüze ihtiyaçları yoktur.
   - Gerçek modül hazır olunca arayüz `USE_MOCKS=0` ile ona geçer. Kodda değişiklik gerekmez.
4. **Küçük ve sık commit.** Her 30–45 dakikada bir `pull --rebase` + `push`.

## 2. Dosya sahipliği

| Kişi | Sadece bu dosyalara yazar |
|---|---|
| **Kişi 1** · Veri ve Model | `scripts/prepare_backblaze.py`, `scripts/train_disk_model.py`, `scripts/make_demo_json.py`, `core/disk_model.py`, `core/smart_parser.py`, `core/nvme_rules.py`, `demo/*.json`, `docs/metrics.md` |
| **Kişi 2** · LLM | `core/config.py`, `core/llm.py`, `core/retrieval.py`, `core/triage.py`, `core/report.py`, `prompts/*`, `scripts/prepare_superuser.py`, `scripts/bench_llm.py`, `docs/timings.md` |
| **Kişi 3** · Arayüz ve Hikâye | `app.py`, `core/mocks.py`, `core/contracts.py`, `README.md`, `requirements.txt`, `LICENSE`, `post/*`, `docs/screenshots/*`, `docs/rehber/*` |

> Yeni bir pip paketi mi lazım? Kişi 3'e yaz; `requirements.txt` dosyasına o ekler.

## 3. Herkesin ilk 15 dakikası (Windows, PowerShell)

```powershell
git clone https://github.com/hacktob3v-devs/disk-doctor.git
cd disk-doctor
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass      # sadece bu pencere için; venv aktive edilebilsin
.venv\Scripts\Activate.ps1
pip install -r requirements.txt                 # tabpfn torch'u da indirir, uzun sürebilir — beklerken rehberini oku
```

Arayüzü mock ile açıp kurulumu doğrula:

```powershell
streamlit run app.py
```

> Bütün komutlar **repo kök klasöründen** çalıştırılır (`disk-doctor/`). Script'ler `python -m scripts.<ad>` ile çalışır; böylece `core` paketi import edilebilir.

## 4. Git akışı (herkes aynı)

```powershell
git pull --rebase                 # önce başkalarının değişikliklerini al
git add core/disk_model.py        # SADECE kendi dosyaların (git add -A KULLANMA)
git commit -m "Disk model: train and predict"
git push
```

Rebase sırasında çatışma çıkarsa:

```powershell
git status                        # çatışan dosyayı gör
# dosyayı düzelt (normalde senin dosyan değilse sahibine sor)
git add <dosya>
git rebase --continue
```

`data/` ve `models/` klasörleri `.gitignore` içinde. Ham veri ve eğitilmiş model **asla** commit'lenmez.

## 5. Zaman çizelgesi ve sync noktaları

| Saat | Ne | Süre |
|---|---|---|
| 19:00 | Başla. Uzun indirmeleri **hemen** başlat (Backblaze, Ollama modeli, pip) | — |
| **19:45** | **SYNC 1** — kurulum durumu, contracts herkes için tamam mı? | 10 dk |
| **21:30** | **SYNC 2** — kill rule kontrolü (indirme / TabPFN / Gemma hızı) | 5 dk |
| **23:30** | **CP1** — her modül tek başına çalışıyor mu? Mock → gerçek geçişi başlar | 10 dk |
| **01:30** | **CP2** — `USE_MOCKS=0` ile uçtan uca çalışıyor → **MLH'ya ilk gönderim** | 15 dk |
| **03:30** | **CP3** — hepsi yeşil mi? Yeşilse COULD özellikler, değilse düzelt | 5 dk |
| **04:30** | **KOD DONDURMA** — sadece hata düzeltme | — |
| 05:15 | Sunum provası (3 dk, kronometreyle) | 15 dk |
| 05:30 | Jüri | — |

Sync toplantısında herkes 3 cümle söyler: **ne bitti / ne bitmek üzere / neye takıldım.** Uzun tartışma yok.

## 6. Kill rule'lar (tartışmadan uygulanır)

| Saat | Durum | Karar |
|---|---|---|
| 21:00 | Backblaze inmedi | Kişi 1 parser + NVMe kurallarına geçer; veri gelince modele döner |
| 21:00 | TabPFN çalışmıyor | RandomForest (`DD_DISK_MODEL=rf`), 03:30'da tekrar dene |
| 22:00 | Gemma cevabı 30 sn'den uzun | Daha küçük Gemma varyantı; benzer vaka 3 → 2 |
| 01:30 | CP2 kaçtı | SHOULD/COULD iptal; çekirdek + yazı + demo kaydı |
| 04:30 | Hâlâ hata var | Hatalı özelliği arayüzden gizle |

## 7. "Bitti" tanımı (06:00)

Temiz bir klondan, **Wi-Fi kapalı** laptopta:

- [ ] `streamlit run app.py` açılıyor (`USE_MOCKS=0`)
- [ ] Türkçe şikâyet → ön teşhis kartı < 30 sn
- [ ] 3 demo JSON + canlı smartctl çıktısı → risk %, renk, bulgular
- [ ] Müşteri raporu oluşuyor ve indiriliyor
- [ ] Kenar çubuğunda "Çevrimdışı ✓ · süre · 0 TL"
- [ ] Kapalı API yok, ham veri repoda yok
