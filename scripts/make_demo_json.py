"""Convert heldout Backblaze snapshots to labelled smartctl-shaped demo JSON.

These are CSV conversions, not live smartctl captures. NVMe fallback is explicitly
synthetic; an existing local NVMe capture is never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import math
from pathlib import Path

import pandas as pd

from core.disk_model import ROOT
from core.smart_parser import parse
from core.nvme_rules import COUNTERS

NAMES = {5: "Reallocated_Sector_Ct", 9: "Power_On_Hours", 187: "Reported_Uncorrect",
         188: "Command_Timeout", 194: "Temperature_Celsius", 197: "Current_Pending_Sector", 198: "Offline_Uncorrectable"}


def to_smartctl(row: pd.Series, serial: str, *, source_sha256: str) -> dict:
    table = []
    for attr_id, name in NAMES.items():
        raw = row.get(f"smart_{attr_id}_raw")
        if pd.notna(raw) and math.isfinite(raw) and raw >= 0:
            table.append({"id": attr_id, "name": name, "raw": {"value": int(raw)}})
    lead = int(row["lead_days"])
    failure_date = row.get("target_failure_date")
    result = {
        "_source": "Backblaze Drive Stats heldout CSV snapshot converted to smartctl JSON shape; NOT a live disk read.",
        "_provenance": {
            "source_url": "https://www.backblaze.com/cloud-storage/resources/hard-drive-test-data",
            "sample_sha256": source_sha256, "snapshot_date": str(row["date"])[:10],
            "target_label": int(row["failure"]), "lead_days": lead,
            "recorded_failure_date": str(failure_date)[:10] if pd.notna(failure_date) else None,
            "selection": "Illustrative heldout example selected by counters, not a representative accuracy test.",
            "original_serial": "redacted",
        },
        "device": {"name": "/dev/sda", "type": "sat", "protocol": "ATA"},
        "model_name": str(row["model"]), "serial_number": serial,
        "ata_smart_attributes": {"table": table},
    }
    capacity = row.get("capacity_bytes")
    if pd.notna(capacity) and math.isfinite(capacity) and capacity >= 0:
        result["user_capacity"] = {"bytes": int(capacity)}
    hours = row.get("smart_9_raw")
    if pd.notna(hours) and math.isfinite(hours) and hours >= 0:
        result["power_on_time"] = {"hours": int(hours)}
    temp = row.get("smart_194_raw")
    if pd.notna(temp) and 0 < temp < 100:
        result["temperature"] = {"current": int(temp)}
    parse(result)
    return result


def sanitized_nvme_capture(raw: dict) -> dict:
    """Allowlist a genuine capture; never export device identifiers or serials."""
    disk = parse(raw)
    if disk["kind"] != "nvme":
        raise ValueError("Canlı NVMe örneği için NVMe smartctl çıktısı gerekli.")
    log = raw["nvme_smart_health_information_log"]
    allowed_log = {key: log[key] for key in (*COUNTERS, "temperature") if key in log}
    result = {
        "_source": "Genuine local read-only smartctl NVMe capture; serial and other unique device identifiers removed.",
        "_provenance": {"kind": "live_capture", "command": "smartctl -j -a -d nvme /dev/sda",
                        "smartctl_version": raw.get("smartctl", {}).get("version"),
                        "identifiers": "allowlisted export; original serial/WWN/EUI/NGUID not included"},
        "device": {"name": "/dev/sda", "type": "nvme", "protocol": "NVMe"},
        "model_name": disk["model"], "serial_number": "DEMO-NVME-001",
        "nvme_smart_health_information_log": allowed_log,
    }
    if "nvme_total_capacity" in raw:
        result["nvme_total_capacity"] = raw["nvme_total_capacity"]
    elif "user_capacity" in raw:
        result["user_capacity"] = {"bytes": raw["user_capacity"]["bytes"]}
    if "power_on_time" in raw:
        result["power_on_time"] = {"hours": disk["power_on_hours"]}
    if disk["temperature_c"] is not None:
        result["temperature"] = {"current": disk["temperature_c"]}
    if "passed" in raw.get("smart_status", {}):
        result["smart_status"] = {"passed": raw["smart_status"]["passed"]}
    if "exit_status" in raw.get("smartctl", {}):
        result["smartctl"] = {"exit_status": raw["smartctl"]["exit_status"]}
    parse(result)
    return result


def make_demos(models: Path | None = None, output: Path | None = None, nvme_source: Path | None = None):
    models = models or ROOT / "models"
    output = output or ROOT / "demo"
    df = pd.read_csv(models / "test_holdout.csv")
    context = pd.read_csv(models / "train_context.csv")
    if set(df.serial_number) & set(context.serial_number):
        raise ValueError("Demo/test diskleri eğitim bağlamıyla çakışıyor.")
    meta = json.loads((models / "model_metadata.json").read_text(encoding="utf-8"))
    for filename, key in [("train_context.csv", "context_sha256"), ("test_holdout.csv", "holdout_sha256")]:
        if hashlib.sha256((models / filename).read_bytes()).hexdigest() != meta.get(key):
            raise ValueError("Model artefaktları farklı çalıştırmalara ait; eğitimi yeniden tamamlayın.")
    # Select by raw warning counters, never by the model's predicted outcome.
    positives = df[df.failure.eq(1)].sort_values(["smart_197_raw", "smart_5_raw", "serial_number"], ascending=[False, False, True], na_position="last")
    negatives = df[df.failure.eq(0)].copy()
    if positives.empty or negatives.empty:
        raise ValueError("Demo için her iki sınıftan bağımsız test diski gerekli.")
    failing = positives.iloc[0]
    same_model = negatives[negatives.model.eq(failing.model)]
    healthy = (same_model if len(same_model) else negatives).sort_values(["smart_197_raw", "smart_5_raw", "serial_number"], na_position="last").iloc[0]
    output.mkdir(parents=True, exist_ok=True)
    for name, row in [("failing_hdd", failing), ("healthy_hdd", healthy)]:
        payload = to_smartctl(row, f"DEMO-{name.upper()}", source_sha256=meta["sample_sha256"])
        path = output / f"{name}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        print(f"{path}: {row['model']}, target_label={int(row.failure)}, lead_days={int(row.lead_days)}")
    nvme_path = output / "my_nvme.json"
    if nvme_source is not None:
        payload = sanitized_nvme_capture(json.loads(nvme_source.read_text(encoding="utf-8-sig")))
        nvme_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        print(f"{nvme_path}: genuine capture; unique identifiers removed")
    elif not nvme_path.exists():
        payload = {
            "_source": "SYNTHETIC NVMe example for UI/rule testing; NOT a live laptop capture or Backblaze observation.",
            "device": {"name": "/dev/nvme0", "type": "nvme", "protocol": "NVMe"},
            "model_name": "Synthetic NVMe SSD 512GB", "serial_number": "DEMO-NVME-001",
            "nvme_total_capacity": 512110190592, "power_on_time": {"hours": 2310},
            "temperature": {"current": 41},
            "nvme_smart_health_information_log": {
                "critical_warning": 0, "temperature": 41, "available_spare": 100,
                "available_spare_threshold": 10, "percentage_used": 7,
                "media_errors": 0, "num_err_log_entries": 0, "power_on_hours": 2310,
            },
        }
        parse(payload)
        nvme_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"{nvme_path}: explicitly synthetic")
    else:
        print(f"{nvme_path}: existing file preserved")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, default=ROOT / "models")
    parser.add_argument("--output", type=Path, default=ROOT / "demo")
    parser.add_argument("--nvme-source", type=Path, help="Read a real local NVMe capture and export only non-identifying fields")
    args = parser.parse_args()
    try:
        make_demos(args.models, args.output, args.nvme_source)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Demo üretilemedi: {exc}\n")


if __name__ == "__main__":
    main()
