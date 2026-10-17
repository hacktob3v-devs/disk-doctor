"""Prepare one row per drive from official daily CSVs or a local quarter ZIP.

Usage: python -m scripts.prepare_backblaze data/data_Q2_2026.zip
Default target: recorded failure exactly one day AFTER the feature snapshot.
No archives are extracted and only required columns are loaded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import numpy as np

from core.disk_model import CRITICAL, ROOT

SMART = ["smart_5_raw", "smart_9_raw", "smart_187_raw", "smart_188_raw", "smart_194_raw", "smart_197_raw", "smart_198_raw"]
COLS = ["date", "serial_number", "model", "capacity_bytes", "failure"] + SMART
SOURCE_URL = "https://www.backblaze.com/cloud-storage/resources/hard-drive-test-data"


@contextmanager
def daily_files(source: Path):
    """Yield sorted (name, open callable) pairs without extracting ZIP paths."""
    if source.is_file() and source.suffix.lower() == ".zip":
        with ZipFile(source) as archive:
            names = sorted(n for n in archive.namelist() if n.endswith(".csv") and "__MACOSX" not in n and Path(n).stem[:4].isdigit())
            yield [(n, lambda n=n: archive.open(n)) for n in names]
    elif source.is_dir():
        files = sorted(p for p in source.rglob("*.csv") if "__MACOSX" not in p.parts and p.stem[:4].isdigit())
        yield [(str(p), lambda p=p: p.open("rb")) for p in files]
    else:
        raise ValueError(f"Günlük CSV klasörü veya ZIP bulunamadı: {source}")


def read_day(opener, columns):
    with opener() as stream:
        frame = pd.read_csv(stream, usecols=lambda c: c in columns, low_memory=False)
    required = {"date", "serial_number", "failure"}
    if not required.issubset(frame):
        raise ValueError("Günlük dosyada date, serial_number veya failure eksik.")
    if frame["serial_number"].isna().any():
        raise ValueError("Günlük dosyada boş seri numarası var.")
    frame["serial_number"] = frame["serial_number"].astype(str)
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
    labels = pd.to_numeric(frame["failure"], errors="raise")
    if not labels.isin([0, 1]).all():
        raise ValueError("failure alanı 0 veya 1 olmalı.")
    frame["failure"] = labels.astype(int)
    if frame.duplicated(["serial_number", "date"]).any():
        raise ValueError("Günlük dosyada aynı diskin aynı gün birden fazla kaydı var.")
    return frame.reindex(columns=columns)


def priority(serial: str, seed: int) -> str:
    return hashlib.sha256(f"{seed}:{serial}".encode()).hexdigest()


def prepare(source: Path, output: Path, *, lead_days: int = 1, healthy_n: int = 3000, healthy_days: int = 8, seed: int = 42):
    if lead_days < 0 or healthy_n < 2 or healthy_days < 1:
        raise ValueError("lead-days >= 0, healthy-n >= 2 ve healthy-days >= 1 gerekli.")
    with daily_files(source) as files:
        if not files:
            raise ValueError(f"Günlük CSV bulunamadı: {source}")
        failures = {}
        last_seen = {}
        day_dates = {}
        print(f"{len(files)} günlük dosya: ilk geçiş, arıza ve gözlem tarihleri", flush=True)
        for i, (name, opener) in enumerate(files, 1):
            day = read_day(opener, ["date", "serial_number", "failure"])
            dates = day.date.unique()
            if len(dates) != 1:
                raise ValueError(f"Her dosya tek bir günü içermeli: {name}")
            date = pd.Timestamp(dates[0])
            if date in day_dates.values():
                raise ValueError(f"Bir gün için birden fazla CSV var: {date}")
            day_dates[name] = date
            for serial in day.loc[day.failure.eq(1), "serial_number"]:
                failures[serial] = min(failures.get(serial, date), date)
            last_seen.update({serial: max(last_seen.get(serial, date), date) for serial in day.serial_number})
            if i % 10 == 0 or i == len(files):
                print(f"  {i}/{len(files)}; arıza kaydı olan disk: {len(failures)}", flush=True)
        # Use exact prior-day rows; never relabel a same-day failure as next-day.
        target_dates = {serial: date - pd.Timedelta(days=lead_days) for serial, date in failures.items()}
        unique_dates = sorted(set(day_dates.values()))
        indices = sorted({round(i * (len(unique_dates)-1) / max(1, healthy_days-1)) for i in range(min(healthy_days, len(unique_dates)))})
        sample_days = {unique_dates[i] for i in indices}
        positive_days = set(target_dates.values())
        positives, controls = [], []
        for i, (name, opener) in enumerate(files, 1):
            date = day_dates[name]
            if date not in sample_days and date not in positive_days:
                continue
            frame = read_day(opener, COLS)
            for col in SMART + ["capacity_bytes"]:
                values = pd.to_numeric(frame[col], errors="coerce")
                frame[col] = values.where(np.isfinite(values) & (values >= 0))
            # A recognized HDD health counter is required. Missing fields remain
            # NaN, not fabricated healthy zeroes; exclude explicitly named SSDs.
            frame = frame[frame[list(CRITICAL)].notna().any(axis=1)]
            frame = frame[~frame.model.fillna("").str.contains(r"SSD|NVMe", case=False, regex=True)]
            wanted = frame.serial_number.map(target_dates).eq(date)
            if lead_days:
                wanted &= frame.failure.eq(0)
            pos = frame.loc[wanted].copy()
            if len(pos):
                pos["source_failure"] = pos.failure
                pos["failure"] = 1
                pos["target_failure_date"] = pos.serial_number.map(failures)
                positives.append(pos)
            if date in sample_days:
                neg = frame[frame.failure.eq(0) & ~frame.serial_number.isin(failures)].copy()
                observed_through = neg.serial_number.map(last_seen)
                neg = neg[observed_through.ge(date + pd.Timedelta(days=lead_days))]
                # Retain a bounded deterministic candidate pool per day.
                neg["_priority"] = neg.serial_number.map(lambda s: priority(s, seed))
                neg = neg.sort_values(["_priority", "serial_number"]).head(healthy_n * 2)
                # Draw a deterministic pseudorandom observation per drive,
                # independent of its drive-selection priority. Earliest-date
                # deduplication would concentrate controls at quarter start.
                neg["_snapshot_priority"] = neg.serial_number.map(
                    lambda s: priority(f"snapshot:{s}:{date.date()}", seed))
                neg["source_failure"] = 0
                neg["target_failure_date"] = pd.NaT
                controls.append(neg)
            print(f"  İkinci geçiş {i}/{len(files)}: {date.date()}, pozitif={len(pos)}", flush=True)
        if not positives or not controls:
            raise ValueError("Hedef ufkunda yeterli arızalı/sağlıklı kayıt yok; gerçek veriyi kontrol edin.")
        pos = pd.concat(positives, ignore_index=True).sort_values("date").drop_duplicates("serial_number")
        neg = pd.concat(controls, ignore_index=True).sort_values(["_priority", "_snapshot_priority", "date"]).drop_duplicates("serial_number").head(healthy_n).drop(columns=["_priority", "_snapshot_priority"])
        if pos.empty or neg.empty:
            raise ValueError("Filtreler sonrası iki sınıfta da gerçek disk kaydı gerekli.")
        frame = pd.concat([pos, neg], ignore_index=True).sort_values("serial_number").reset_index(drop=True)
        if frame.serial_number.duplicated().any():
            raise ValueError("Örneklemde seri numarası tekrarı var.")
        frame["lead_days"] = lead_days
        output.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(output, index=False)
        metadata = {
            "source": str(source.resolve()), "source_url": SOURCE_URL,
            "target": "failure on snapshot date" if lead_days == 0 else f"recorded failure exactly {lead_days} day(s) after snapshot",
            "lead_days": lead_days, "daily_files": len(files),
            "date_start": str(min(unique_dates).date()), "date_end": str(max(unique_dates).date()),
            "failed_drives_in_source": len(failures), "positive_rows": len(pos), "negative_rows": len(neg),
            "seed": seed, "missing_values": "preserved; training-only imputation",
            "control_sampling": "serial-hash drive selection; independent serial/date hash selects one eligible snapshot per drive",
            "control_snapshot_dates": neg.date.dt.strftime("%Y-%m-%d").value_counts().sort_index().to_dict(),
            "negative_definition": "no recorded failure in available quarter; observed at least lead_days after snapshot; not proof of future health",
            "sample_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        }
        output.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(json.dumps(metadata, indent=2), flush=True)
        return frame, metadata


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, nargs="?", default=ROOT / "data" / "backblaze_raw")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "drives_sample.csv")
    parser.add_argument("--lead-days", type=int, default=1)
    parser.add_argument("--healthy-n", type=int, default=3000)
    parser.add_argument("--healthy-days", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    try:
        prepare(args.source, args.output, lead_days=args.lead_days, healthy_n=args.healthy_n, healthy_days=args.healthy_days, seed=args.seed)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Veri hazırlanamadı: {exc}\n")


if __name__ == "__main__":
    main()
