<!--
TASLAK — DEV'e submission template ile yapıştırılacak.
[KÖŞELİ PARANTEZ] içindekiler tamirci görüşmesinden ya da ekip arkadaşlarından gelecek GERÇEK bilgilerle doldurulacak.
Hiçbir rakamı uydurma. Bilgi gelmezse cümleyi çıkar.

Kazanan yazılardan (RESIDUES, ECHOLALIA) aldığımız yapı:
- İlk cümle: tek cümlelik kanca
- İsim verilmiş tasarım ilkesi ("See It Coming, Keep It Local")
- Ne-ne-yapar tablosu
- Ayrı "temaya nasıl bağlanıyor" bölümü
- Jürinin itirazını önceden cevaplayan bölüm ("On the numbers")
- "A note for judges": nasıl çalıştırılır, ne çevrimdışı çalışır
- Her ödül kategorisi için ayrı gerekçe
- Kullanılan araçlarda tam şeffaflık
-->

*This is a submission for the Hacktoberfest 2026 DEV Challenge — Week 2: Side Hustle.*

# DiskDoctor: The Repair Shop That Sees the Disk Dying First

## What I Built

**DiskDoctor tells a neighborhood computer repair shop which hard drive is about to die — before the customer loses everything on it — and it does it on the shop's own laptop, with the Wi-Fi off.**

<!-- SAHNE: tamircinin gerçek hikâyesi. Örnek iskelet, gerçek bilgilerle değiştir: -->
[Name / "A repair shop owner"] runs a small computer repair shop in Elazığ, Türkiye. Every month, about **[X]** customers walk in with a laptop that won't boot and a disk that has already taken their [photos / thesis / invoices] with it. *"[Real quote from the call, translated]"*, he told us. Sending a dead disk to a data-recovery lab costs around **[Y] TL**, more than many customers are willing to pay.

The fix isn't magic. Most dying disks **say so** weeks in advance, in their S.M.A.R.T. counters: reallocated sectors, sectors the disk can no longer read, uncorrectable errors. Nobody in a small shop reads those numbers, so the warning goes unheard.

DiskDoctor gives the technician two tools:

| Tool | What it does | What runs it |
|---|---|---|
| 🩺 **Triage card** | The customer's complaint goes in, in their own words, in Turkish. Out come the likely faulty parts, a cheap-to-expensive check order, the questions to ask, and similar real cases from Super User. | **Gemma 4**, local via Ollama, JSON-schema output, plus a small TF-IDF retrieval over Super User Q&A |
| 💽 **Disk health** | Load the `smartctl -j` report of any disk → a failure-risk score, the readings that drove it, and a plain-language report the customer can take home. | **TabPFN** trained on real drive failures from **Backblaze Drive Stats** (rule-based score for NVMe), report text by **Gemma 4** |

The design principle is **"See It Coming, Keep It Local"**: the earlier the shop sees a failing disk, the more it can save for the customer, and none of that customer's data ever leaves the counter.

<!-- GIF 1: Wi-Fi kapatma + ön teşhis kartı -->
<!-- GIF 2: failing_hdd.json → kırmızı kart → müşteri raporu -->

## How it connects to the theme

The brief asked for something *small, specific and useful* that a real person would actually pay for. A neighborhood repair shop already makes money on exactly one thing here: replacing a disk and moving the data, which is only possible **while the disk is still alive**. Every failing disk DiskDoctor flags early becomes a [disk replacement + backup] job instead of a lost customer and a lost archive.

When we asked what he'd pay for it, he said: *"[Answer from the call]"*.

## Why open beats a closed API here

<!-- Kişi 2'nin taslağı + docs/timings.md tablosu buraya -->
- **Cost that scales with customers.** With a hosted API, every triage and every report would be a paid request. With local Gemma, the marginal cost per customer is **zero**.
- **Customer data stays in the shop.** Serial numbers, what's on the disk, what the customer said: none of it leaves the machine.
- **The internet is the least reliable part of a small shop.** We turned Wi-Fi off for the whole demo. Triage took **[X s]**, the report **[Y s]** on a **[laptop model, CPU, RAM, no GPU]**.
- **No lock-in.** The weights live on the disk; a price change somewhere else doesn't change the shop's tool.
- **The core isn't a chatbot.** The risk number comes from a tabular model trained on real failures, which a general chat API can't do from a S.M.A.R.T. table.

| Step | Average | Worst |
|---|---|---|
| Triage (incl. retrieval) | [ ] | [ ] |
| Customer report | [ ] | [ ] |

## How it works

<!-- Mimari diyagram görseli: docs/screenshots/architecture.png -->

<!-- Kişi 1'in "How it works — the disk model" taslağı buraya -->

<!-- Kişi 2: Gemma JSON şema + benzer vaka arama + "sayıları kod yazar, Gemma sadece metni" kuralı -->

**The rule we kept:** every number in the customer report is written by code, not by the model. Gemma only writes the explanation, so it can't invent a risk percentage.

## On the numbers

<!-- Jüride veri bilimciler var: itirazı önceden cevapla. Kişi 1'in "Honest limitations" taslağı + docs/metrics.md tablosu -->
Some of you will ask how good the disk model really is. Here are the held-out results, split by drive serial number so the model never sees the same physical drive twice:

| Metric | Value |
|---|---|
| Recall (failing drives caught) | [ ] |
| Precision | [ ] |
| ROC-AUC | [ ] |

And here's what those numbers don't tell you:
- [Kişi 1'in maddeleri]

## Our first user

<!-- Pazar günü tamircinin yüz yüze tepkisi + gece kullandırdığımız kişinin cümlesi -->

## A note for judges

Everything runs offline once the models are downloaded:

```bash
git clone https://github.com/hacktob3v-devs/disk-doctor.git
cd disk-doctor
pip install -r requirements.txt
ollama pull [gemma4 tag]
python -m scripts.prepare_backblaze data/backblaze_raw
python -m scripts.train_disk_model
streamlit run app.py
```

The `demo/` folder has three ready disks: a healthy HDD, an HDD that **really failed the next day** (taken from Backblaze data), and an NVMe SSD. To check your own disk, run `smartctl -j -a /dev/sda > disk.json` as administrator and upload the file.

## How we built it

<!-- GitHub Copilot kullanımı + DevRelay oturumu gömülü. Kullanılan tüm araçları açıkça yaz. -->
We wrote the code with **GitHub Copilot**. Here is a recorded agent session: [DevRelay embed].

## What's next

- Log the shop's own drives and what happened to them, and refit the model on that data
- Voice input for complaints (faster-whisper, also local)
- Repair guides for the suspected part

## Prize categories

- **Gemma**: runs the triage card and the customer report on the shop's laptop, offline, with JSON-schema output.
- **TabPFN**: the failure-risk model, trained on real Backblaze drive failures in seconds on a CPU.
- **GitHub Copilot**: used throughout the build; session recorded with DevRelay.

## Team & links

- Team: [@devuser1], [@devuser2], [@devuser3]
- Code: https://github.com/hacktob3v-devs/disk-doctor (MIT)
- Data: Backblaze Drive Stats (attributed), Super User Q&A (CC BY-SA 4.0, every case linked)
