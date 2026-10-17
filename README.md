# DiskDoctor

**An offline assistant that tells a neighborhood repair shop which hard drive is about to die — before the customer loses their data.**

> Built at Hacktoberfest Hack Day Elazığ 2026 · DEV Week 2 challenge: *Side Hustle*

A small computer repair shop asks the same questions to every customer and has to *guess* whether a disk is healthy. DiskDoctor gives the technician two things, running entirely on the shop's own laptop:

1. **Triage card** — the customer's complaint goes in, likely faulty parts, a check order and follow-up questions come out (Gemma 4, local via Ollama).
2. **Disk health** — load a `smartctl -j` report and get a failure-risk score (TabPFN trained on real Backblaze drive failures; rule-based score for NVMe drives), plus a plain-language report for the customer.

No closed APIs. No per-request cost. Works with Wi-Fi off.

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
- Local latency, measured with Wi-Fi off: [docs/timings.md](docs/timings.md)

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
- Super User Q&A via Stack Exchange Data Explorer — CC BY-SA 4.0, source link kept for every example

Raw data and trained models are not committed; the Quick start shows how to rebuild them.

## Limitations

_To be written: Backblaze data comes from data-center drives, NVMe drives use a rule-based score, and the triage is a suggestion, not a replacement for the technician._

## License

MIT — see [LICENSE](LICENSE).
