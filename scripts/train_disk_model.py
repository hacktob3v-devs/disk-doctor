"""Freeze a drive-disjoint holdout, evaluate local models, save training context.

Usage: python -m scripts.train_disk_model --method compare
No quality metric is produced without real input data. RF is the baseline.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, confusion_matrix, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from core.disk_model import CONTEXT_PATH, FEATURES, ROOT, fit_on, make_features, validate_context


def metrics(y, p, threshold=0.60):
    pred = p >= threshold
    return {
        "threshold": threshold, "recall": float(recall_score(y, pred, zero_division=0)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, p)),
        "average_precision": float(average_precision_score(y, p)),
        "confusion_matrix": confusion_matrix(y, pred, labels=[0, 1]).tolist(),
    }


def confidence_intervals(y, p, seed=42):
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(300):
        ids = rng.integers(0, len(y), len(y))
        if len(np.unique(y[ids])) == 2:
            row = metrics(y[ids], p[ids])
            samples.append([row[k] for k in ("recall", "precision", "roc_auc")])
    bounds = np.quantile(samples, [0.025, 0.975], axis=0)
    return {key: [float(bounds[0, i]), float(bounds[1, i])] for i, key in enumerate(("recall", "precision", "roc_auc"))}


def split_data(df, n_per_class=480, seed=42, *, test_after: str | None = None):
    validate_context(df)
    counts = df.failure.astype(int).value_counts()
    if min(counts) < 4:
        raise ValueError("Ayrı eğitim/test için her sınıfta en az dört farklı disk gerekli.")
    if test_after is None:
        train, test = train_test_split(df, test_size=0.25, stratify=df.failure, random_state=seed)
    else:
        if "date" not in df or "lead_days" not in df:
            raise ValueError("Zamansal ayrım için date ve lead_days gerekli.")
        dates = pd.to_datetime(df.date, errors="raise")
        cutoff = pd.Timestamp(test_after).normalize()
        # A training target must be observable by the cutoff, not just its X.
        label_observable = dates + pd.to_timedelta(df.lead_days, unit="D")
        train = df[label_observable.le(cutoff)]
        test = df[dates.gt(cutoff)]
        if set(train.failure.unique()) != {0, 1} or set(test.failure.unique()) != {0, 1}:
            raise ValueError("Zamansal eğitim ve testte her iki sınıf da gerekli.")
    context = pd.concat([
        train[train.failure.eq(label)].sample(min(n_per_class, int(train.failure.eq(label).sum())), random_state=seed)
        for label in (0, 1)
    ]).sample(frac=1, random_state=seed)
    if set(context.serial_number) & set(test.serial_number):
        raise ValueError("Eğitim/test seri numarası sızıntısı tespit edildi.")
    return context.reset_index(drop=True), test.reset_index(drop=True)


def train(source: Path, *, method="compare", n_per_class=480, seed=42, output_dir: Path | None = None, report: Path | None = None, test_after: str | None = None):
    if n_per_class < 2 or n_per_class > 500:
        raise ValueError("CPU bağlamı için sınıf başına 2–500 satır kullanın.")
    output_dir = output_dir or CONTEXT_PATH.parent
    report = report or ROOT / "docs" / "metrics.md"
    df = pd.read_csv(source)
    if "lead_days" not in df or df.lead_days.nunique() != 1 or df.lead_days.isna().any():
        raise ValueError("Hedef tanımı eksik: önce prepare_backblaze ile tek bir lead_days değeri üretin.")
    lead_days = int(df.lead_days.iloc[0])
    preparation_path = source.with_suffix(".metadata.json")
    preparation = json.loads(preparation_path.read_text(encoding="utf-8")) if preparation_path.exists() else {}
    if preparation and preparation.get("sample_sha256") != hashlib.sha256(source.read_bytes()).hexdigest():
        raise ValueError("Örneklem dosyası hazırlama metadata hash'i ile eşleşmiyor.")
    if lead_days < 0:
        raise ValueError("lead_days negatif olamaz.")
    context, test = split_data(df, n_per_class, seed, test_after=test_after)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir
    # A failed experiment leaves its staging directory as evidence, without
    # replacing the previous usable context, holdout or metadata.
    output_dir = Path(tempfile.mkdtemp(prefix=".training-", dir=destination))
    # Freeze identities BEFORE evaluating either model. These files remain local.
    split_manifest = {"seed": seed, "test_after": test_after, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                      "train_serials": sorted(context.serial_number.tolist()), "test_serials": sorted(test.serial_number.tolist())}
    (output_dir / "split_ids.json").write_text(json.dumps(split_manifest, indent=2), encoding="utf-8")
    test.to_csv(output_dir / "test_holdout.csv", index=False)
    y = test.failure.to_numpy(dtype=int)
    x = make_features(test)
    results, errors = {}, {}
    methods = ["rf", "tabpfn"] if method == "compare" else [method]
    for name in methods:
        try:
            print(f"{name}: {len(context)} bağlam / {len(test)} test diski", flush=True)
            t0 = time.perf_counter()
            clf, actual = fit_on(context, name, allow_fallback=False)
            fit_s = time.perf_counter() - t0
            t0 = time.perf_counter()
            p = clf.predict_proba(x)[:, list(clf.classes_).index(1)]
            predict_s = time.perf_counter() - t0
            if not np.isfinite(p).all() or not ((0 <= p) & (p <= 1)).all():
                raise ValueError("Model geçersiz skorlar üretti.")
            row = metrics(y, p)
            row.update({"fit_seconds": fit_s, "predict_batch_seconds": predict_s,
                        "ci95": confidence_intervals(y, p, seed),
                        "thresholds": [metrics(y, p, t) for t in (0.30, 0.50, 0.60)]})
            results[actual] = row
            pd.DataFrame({"serial_number": test.serial_number, "label": y, "score": p}).to_csv(output_dir / f"predictions_{actual}.csv", index=False)
            print(json.dumps({actual: row}), flush=True)
        except Exception as exc:
            errors[name] = f"{type(exc).__name__}: {exc}"
            print(f"{name} başarısız: {errors[name]}", flush=True)
    if not results and method == "tabpfn":
        print("TabPFN kullanılamadı; gerçek RF yedeği ayrı değerlendirilir.", flush=True)
        t0 = time.perf_counter()
        clf, _ = fit_on(context, "rf", allow_fallback=False)
        fit_s = time.perf_counter() - t0
        t0 = time.perf_counter()
        p = clf.predict_proba(x)[:, list(clf.classes_).index(1)]
        row = metrics(y, p)
        row.update({"fit_seconds": fit_s, "predict_batch_seconds": time.perf_counter()-t0,
                    "ci95": confidence_intervals(y, p, seed), "thresholds": [metrics(y, p, t) for t in (0.30, 0.50, 0.60)]})
        results["rf"] = row
        pd.DataFrame({"serial_number": test.serial_number, "label": y, "score": p}).to_csv(output_dir / "predictions_rf.csv", index=False)
    if not results:
        raise RuntimeError("Hiçbir model değerlendirilemedi: " + json.dumps(errors))
    # Keep model choice explicit. This is a small heldout comparison, not a claim
    # of statistical superiority and not threshold tuning on the holdout.
    selected = "tabpfn" if "tabpfn" in results else "rf"
    context.to_csv(output_dir / "train_context.csv", index=False)
    versions = {}
    for package in ("numpy", "pandas", "scikit-learn", "tabpfn", "torch"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not installed"
    metadata = {"source": str(source.resolve()), "sample_sha256": split_manifest["source_sha256"],
                "context_sha256": hashlib.sha256((output_dir / "train_context.csv").read_bytes()).hexdigest(),
                "holdout_sha256": hashlib.sha256((output_dir / "test_holdout.csv").read_bytes()).hexdigest(),
                "selected": selected, "lead_days": lead_days, "seed": seed, "features": FEATURES,
                "test_after": test_after,
                "train_n": len(context), "train_positive": int(context.failure.sum()),
                "test_n": len(test), "test_positive": int(y.sum()), "results": results, "failures": errors,
                "negative_snapshot_dates": df.loc[df.failure.eq(0), "date"].value_counts().to_dict() if "date" in df else {},
                "control_sampling": preparation.get("control_sampling", "unspecified; see source provenance"),
                "versions": versions, "platform": platform.platform(), "python": platform.python_version()}
    checkpoint = ROOT / "models" / "tabpfn-v2-classifier.ckpt"
    if checkpoint.is_file():
        metadata["checkpoint_sha256"] = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    (output_dir / "model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    staged_report = output_dir / report.name
    write_report(metadata, staged_report)
    staged_plot = output_dir / "confusion_matrix.png"
    write_plot(metadata, staged_plot)
    report.parent.mkdir(parents=True, exist_ok=True)
    os.replace(staged_plot, report.with_name(report.stem + "_confusion_matrix.png"))
    os.replace(staged_report, report)
    for artifact in output_dir.iterdir():
        if artifact.name != "model_metadata.json":
            os.replace(artifact, destination / artifact.name)
    os.replace(output_dir / "model_metadata.json", destination / "model_metadata.json")
    output_dir.rmdir()
    print(f"Bağlam: {destination / 'train_context.csv'}\nMetrikler: {report}\nEtkin model: {selected}", flush=True)
    return metadata


def write_plot(metadata, path):
    """Plot measured counts only; one panel per actually evaluated method."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from sklearn.metrics import ConfusionMatrixDisplay
    results = metadata["results"]
    fig, axes = plt.subplots(1, len(results), figsize=(5 * len(results), 4.5), squeeze=False)
    for ax, (method, row) in zip(axes[0], results.items()):
        display = ConfusionMatrixDisplay(np.array(row["confusion_matrix"]), display_labels=["No recorded failure", "Recorded failure"])
        display.plot(ax=ax, colorbar=False, cmap="Blues", values_format="d")
        ax.set_title(f"{method} | red threshold 0.60")
        ax.set_xlabel("Prediction")
        ax.set_ylabel("Observed target")
    fig.suptitle(f"Heldout physical drives: n={metadata['test_n']} | lead={metadata['lead_days']} day(s)")
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def write_report(m, path):
    lead = m["lead_days"]
    target = f"SMART snapshot exactly **{lead} day(s) before a recorded failure**" if lead else "SMART snapshot on the recorded failure date (not early warning)"
    lines = ["# Disk model: measured evaluation and Person 1 handoff", "",
             "## Target and evidence", "", f"- Target: {target}.",
             "- Source: [Backblaze Drive Stats](https://www.backblaze.com/cloud-storage/resources/hard-drive-test-data). Raw data, serials and context stay outside Git.",
             f"- Sample SHA-256: `{m['sample_sha256']}`; seed `{m['seed']}`.",
             f"- Context: {m['train_n']} unique drives ({m['train_positive']} positive). Holdout: {m['test_n']} drives ({m['test_positive']} positive). No serial overlap.",
             ("- One snapshot per drive, stratified random split by physical drive identity; NOT a chronological, unseen-manufacturer or repair-shop validation." if not m.get("test_after") else f"- Calendar sensitivity check: training snapshot + target horizon <= {m['test_after']}; test snapshots > {m['test_after']}. Drive identities remain disjoint. Controls were selected retrospectively using quarter outcomes; this is NOT prospective or repair-shop validation."),
             "- Fixed red threshold 0.60, yellow threshold 0.30. Imputation is fitted on context only. Confidence intervals: 300 drive-level bootstrap resamples.",
             "- Negatives have no recorded failure within the available quarter, and were observed at least the target horizon beyond their snapshot. This is not proof of future health.",
             "", "## Heldout results (red threshold = 0.60)", "",
             "| Method | Recall (95% CI) | Precision (95% CI) | ROC-AUC (95% CI) | Average precision | Fit s | Holdout batch s |",
             "|---|---|---|---|---|---|---|"]
    for method, r in m["results"].items():
        cells = [method]
        for k in ("recall", "precision", "roc_auc"):
            low, high = r["ci95"][k]
            cells.append(f"{r[k]:.3f} ({low:.3f}–{high:.3f})")
        cells += [f"{r['average_precision']:.3f}", f"{r['fit_seconds']:.2f}", f"{r['predict_batch_seconds']:.2f}"]
        lines.append("| " + " | ".join(cells) + " |")
    for method, r in m["results"].items():
        tn, fp = r["confusion_matrix"][0]
        fn, tp = r["confusion_matrix"][1]
        lines += ["", f"### {method}: confusion matrix", "", "| Actual / prediction | Non-red | Red |", "|---|---|---|", f"| No recorded failure | {tn} | {fp} |", f"| Recorded failure | {fn} | {tp} |", "", "| Fixed threshold | Recall | Precision |", "|---|---|---|"]
        lines += [f"| {v['threshold']:.2f} | {v['recall']:.3f} | {v['precision']:.3f} |" for v in r["thresholds"]]
    lines += ["", "## Model availability", "", f"- Evaluated selection: **{m['selected']}**. Set `DD_DISK_MODEL={m['selected']}` on the demo laptop.",
              "- RF is the credible classical baseline. No measured result is fabricated for unavailable TabPFN. Default runtime attempts a local checkpoint and warns before using RF.",
              "- TabPFN provisioning: install package, place an official compatible checkpoint at `models/tabpfn-v2-classifier.ckpt` or set `DD_TABPFN_PATH`. Model inference never intentionally downloads weights."]
    for name, failure in m["failures"].items():
        lines.append(f"- Failed experiment `{name}`: {failure}")
    if {"rf", "tabpfn"}.issubset(m["results"]):
        rf, tab = m["results"]["rf"], m["results"]["tabpfn"]
        lines += [f"- Tradeoff: TabPFN is retained for the requested local-model demo. Compared with RF, observed recall difference is {tab['recall']-rf['recall']:+.3f} and precision difference is {tab['precision']-rf['precision']:+.3f}; compare the CPU batch times above. This is **not evidence of established TabPFN superiority**. Both local paths remain available without API costs."]
    lines += ["", "## How it works (article handoff)", "",
              "We use Backblaze's daily drive observations to form one snapshot per physical drive. Positive snapshots precede the recorded failure by the stated horizon; controls have no recorded failure in the observed quarter and at least that much follow-up. We freeze a serial-disjoint holdout before evaluation, then retain a bounded training context for each class.",
              "", "The input consists of five log-transformed SMART error counters, five nonzero flags, temperature and log working hours. Missing values remain missing until a training-only median imputer adds explicit missingness indicators. A classical RandomForest provides the baseline. TabPFN runs locally on CPU with an explicit v2 checkpoint and two estimators; the shared Risk contract records which model actually ran. The saved CSV is the context used to rebuild the model on the demo laptop, not a serialized executable model."]
    lines += ["", "## Honest limitations (copy for the article)", "",
              "Backblaze data-center HDDs differ from laptop and repair-shop drives. Our sampled case/control mix is enriched for failures: the classifier score is **not a calibrated probability** that a shop customer's drive will fail tomorrow. Random drive-level splitting prevents identity leakage but does not establish performance on future periods or unseen drive models. Missingness and vendor-specific SMART encoding can affect predictions. Some failures have little warning in these counters; a low score is not a safety guarantee and backups remain necessary.",
              "", "NVMe uses a transparent **heuristic health score**, not the HDD classifier or a measured failure probability. Counter descriptions in `drivers` are observed findings, not causal feature attributions or SHAP explanations. Synthetic NVMe examples are labelled synthetic. Backblaze examples are converted CSV snapshots, not live smartctl captures; demo selection does not measure accuracy.",
              "", "## Integration for Persons 2 and 3", "",
              "- Public signatures and shared contracts are unchanged. `load_model()` returns `(classifier, method)`; `parse()` returns `DiskInfo`; ATA uses `predict()`, NVMe uses `nvme_rules.score()`.",
              "- Show **model score** for ATA and **rule-based health score** for NVMe, not a calibrated failure percentage. Customer reports must use the same wording; this requires the owners of `app.py` and `core/report.py`.",
              "- Catch `ValueError` / `FileNotFoundError` at the UI boundary. Do not show green for a failed parse or missing model. A partial NVMe log is at least yellow.",
              "- Copy `models/train_context.csv` to the demo laptop through a private transfer; it is deliberately ignored by Git. Install the recorded dependencies before turning off Wi-Fi.",
              "- Tests: `python -m pytest tests -q` (pytest is a development dependency). These are synthetic boundary/pipeline tests, separate from the real-data metrics above.",
              "- Commands from repo root: `python -m scripts.prepare_backblaze data/data_Q2_2026.zip`; `python -m scripts.train_disk_model --method compare`; `python -m scripts.make_demo_json`.",
              "- Scope: Person 1 modules verified separately; full UI/Gemma flow belongs to Persons 2/3. Live capture evidence, if available, is recorded separately below; these metrics do not imply a Wi-Fi-off UI run or user trial.",
              "", "## Reproduction environment", "", f"- Python {m['python']}; {m['platform']}",
              f"- Versions: `{json.dumps(m['versions'], sort_keys=True)}`.", ""]
    if m.get("negative_snapshot_dates"):
        dates = m["negative_snapshot_dates"]
        first_date, count = max(dates.items(), key=lambda item: item[1])
        lines += ["## Control sampling and remaining limitations", "",
                  f"Sampling rule: {m.get('control_sampling', 'unspecified')}. The largest date group contains **{count} of {sum(dates.values())} controls ({first_date})**. Snapshots are limited to selected observation days, not all daily observations. This is still a retrospective case/control experiment; prospective temporal and repair-shop validation remain necessary.",
                  "", "| Control snapshot date | Drives |", "|---|---|", *[f"| {date} | {n} |" for date, n in sorted(dates.items())], ""]
    if "checkpoint_sha256" in m:
        lines += [f"- Local TabPFN checkpoint SHA-256: `{m['checkpoint_sha256']}`.",
                  "- Checkpoint source: [official Prior Labs TabPFN-v2-clf](https://huggingface.co/Prior-Labs/TabPFN-v2-clf). Weights have their own model license, separate from this repository's MIT code license.", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    lines += [f"![Measured confusion matrices]({path.stem}_confusion_matrix.png)", ""]
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "data" / "drives_sample.csv")
    parser.add_argument("--method", choices=["rf", "tabpfn", "compare"], default="compare")
    parser.add_argument("--n-per-class", type=int, default=480)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-after", help="Optional calendar cutoff YYYY-MM-DD for a separate sensitivity check")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        train(args.source, method=args.method, n_per_class=args.n_per_class, seed=args.seed, output_dir=args.output_dir, report=args.report, test_after=args.test_after)
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(1, f"Eğitim tamamlanamadı: {exc}\n")


if __name__ == "__main__":
    main()
