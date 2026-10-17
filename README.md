# DiskDoctor

**A local assistant prototype for small computer repair shops: source-backed troubleshooting, with optional disk-health evidence.**

> Built at Hacktoberfest Hack Day Elazığ 2026 · DEV Week 2 challenge: *Side Hustle*

A repair shop repeatedly collects symptoms, looks up similar cases and explains findings to customers. DiskDoctor targets that workflow on the shop's own laptop. The proposed RAG-first flow and the optional disk assessment have different implementation states:

1. **Source-backed triage and customer report — planned.** Retrieval and local Gemma modules are not yet present in this revision; the UI falls back to mock responses.
2. **Disk assessment — implemented and measured separately.** Load a `smartctl -j` report for a local CPU TabPFN/RF score on HDD data, or transparent NVMe health rules. Neither score is a calibrated real-world failure probability. The UI accepts reports; it does not automatically scan physical disks or read user documents.

Disk-module experiments ran with network connections blocked. Full UI/Gemma offline verification remains pending. Local inference targets no cloud API charge per request; hardware and maintenance still have costs. STT and TTS are outside the first prototype.

## Project status and Turkish jury guide

- [Current state and local assets](docs/PROJECT_STATE.md)
- [Detailed explanation, proposed RAG-first scope and jury questions (Turkish)](docs/PROJE_REHBERI.md)
- [Presentation preparation PDF (Turkish)](output/pdf/DiskDoctor_Juri_Hazirlik.pdf)

`USE_MOCKS=0` uses available real modules but still falls back to mocks for missing modules. The current UI's percentage-based “failure risk” wording must be corrected before making probability claims. Existing submission drafts need the same implementation/status review before publication.

## Completed: Person 1 — data and disk models

- Prepared real Backblaze Q2 2026 data: 1,164 snapshots one day before a recorded failure and 3,000 controls, with one row per drive. Fixed control-date sampling and kept drive identities separate between training and test.
- Implemented local CPU TabPFN-v2 inference with a RandomForest fallback, validated ATA/NVMe parsing, and transparent NVMe health rules.
- Added two heldout HDD demos and a genuine read-only NVMe capture with unique device identifiers removed. **63 synthetic tests pass**; model evaluation and the three-demo journey also ran with socket connections blocked.
- Measured TabPFN ROC-AUC: **0.927** on 1,041 heldout drives; **0.879** in a separate 1,124-drive June calendar check. Full results, historical corrections and setup/handoff notes: [evaluation report](docs/metrics.md).

Person 1 modules are ready for team integration. Full Gemma/Streamlit integration and a repair-shop user trial remain pending; these scores are not calibrated real-world failure probabilities.

## Quick start

Requirements: Python 3.10+, [Ollama](https://ollama.com), and [smartmontools](https://www.smartmontools.org) if you want to read your own disk.

```bash
git clone https://github.com/hacktob3v-devs/disk-doctor.git
cd disk-doctor
python -m venv .venv
.venv\Scripts\activate                 # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
ollama pull <gemma4-tag>               # set the same name in DD_MODEL
```

Prepare the disk model once (download one quarter of [Backblaze Drive Stats](https://www.backblaze.com/drivestats) and unzip it into `data/backblaze_raw/`):

```bash
python -m scripts.prepare_backblaze data/backblaze_raw
python -m scripts.train_disk_model
```

Run the app with the real models:

```powershell
$env:USE_MOCKS="0"                     # macOS/Linux: export USE_MOCKS=0
streamlit run app.py
```

Without `USE_MOCKS=0` the UI runs on mock data, which is handy for working on the interface alone.

### Read your own disk

Run as administrator:

```bash
smartctl --scan
smartctl -j -a /dev/sda > disk.json    # on Windows PowerShell use: cmd /c "smartctl -j -a /dev/sda > disk.json"
```

Upload `disk.json` in the **Disk Sağlığı** tab, or pick one of the files in `demo/`.

## Results

- Disk model test metrics: [docs/metrics.md](docs/metrics.md)
- Full UI/Gemma offline latency: not yet measured in this revision. Disk-module timing evidence is in [docs/metrics.md](docs/metrics.md).

## Project layout

```
app.py              Streamlit UI
core/contracts.py   Shared data types every module follows
core/mocks.py       Fake responses so the UI works before the models do
core/               llm, triage, retrieval, report, disk_model, smart_parser, nvme_rules
prompts/            System prompts
scripts/            Data preparation scripts
demo/               Sample smartctl JSON files for the demo
docs/               Metrics and screenshots
```

## Data sources

- Backblaze Drive Stats — https://www.backblaze.com/drivestats (attribution given; raw data not committed)
- Planned Super User Q&A via Stack Exchange Data Explorer — preserve attribution and the applicable revision-specific CC BY-SA license; this dataset is not yet present.

Raw data, training context and model weights are not committed. The Quick start shows how to rebuild them; for moving them to the demo laptop, see the [demo laptop handoff](docs/metrics.md#demo-laptop-handoff).

## Limitations

Backblaze data-center drives do not establish performance on repair-shop laptops. The calendar evaluation is retrospective, and performance drops on later dates. NVMe uses heuristic rules, not a learned failure-probability model. Results support a prototype and a technician's second opinion; field effectiveness remains unverified.

## License

MIT — see [LICENSE](LICENSE).
