# DiskDoctor

**An offline assistant that tells a neighborhood repair shop which hard drive is about to die — before the customer loses their data.**

> Built at Hacktoberfest Hack Day Elazığ 2026 · DEV Week 2 challenge: *Side Hustle*

A small computer repair shop asks the same questions to every customer and has to *guess* whether a disk is healthy. DiskDoctor gives the technician two things, running entirely on the shop's own laptop:

1. **Triage card** — the customer's complaint goes in, likely faulty parts, a check order and follow-up questions come out (Gemma 4, local via Ollama).
2. **Disk health** — load a `smartctl -j` report and get a failure-risk score (TabPFN trained on real Backblaze drive failures; rule-based score for NVMe drives), plus a plain-language report for the customer.

No closed APIs. No per-request cost. Works with Wi-Fi off.

## Quick start

```bash
git clone https://github.com/hacktob3v-devs/disk-doctor.git
cd disk-doctor
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
ollama pull <gemma4-model>      # set the same name in DD_MODEL
streamlit run app.py
```

The UI runs on mock data until the real modules are ready (`USE_MOCKS=1` is the default). Set `USE_MOCKS=0` to use the real models.

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

Raw data and trained models are not committed; see `scripts/download_data.md`.

## Limitations

_To be written: Backblaze data comes from data-center drives, NVMe drives use a rule-based score, and the triage is a suggestion, not a replacement for the technician._

## License

MIT — see [LICENSE](LICENSE).
