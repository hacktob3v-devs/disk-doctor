"""Explainable local NVMe health heuristics, not failure probabilities."""
import math
import re

from core.contracts import DiskInfo, Risk, level_for

REQUIRED = ("critical_warning", "media_errors", "available_spare",
            "available_spare_threshold", "percentage_used")
COUNTERS = (*REQUIRED, "power_on_hours", "power_cycles", "unsafe_shutdowns",
            "num_err_log_entries", "data_units_read", "data_units_written",
            "host_reads", "host_writes", "controller_busy_time",
            "warning_temp_time", "critical_comp_time",
            "thermal_temp_1_transition_count", "thermal_temp_2_transition_count",
            "thermal_temp_1_total_time", "thermal_temp_2_total_time")


def _integer(value, field: str, maximum=None, minimum=0) -> int:
    """Validate integer-valued JSON counters without lossy coercion."""
    if isinstance(value, bool):
        raise ValueError(f"{field}: tam sayı bekleniyor.")
    if isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value.strip()):
        value = int(value)
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field}: tam sayı bekleniyor.")
    if isinstance(value, float) and (not math.isfinite(value) or not value.is_integer()):
        raise ValueError(f"{field}: sonlu bir tam sayı bekleniyor.")
    value = int(value)
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{field}: değer izin verilen aralığın dışında.")
    return value


def _temperature(value, field="temperature_c") -> int:
    return _integer(value, field, maximum=200, minimum=-60)


def _validated_log(log) -> dict:
    """Keep vendor fields while validating all supported health counters."""
    if not isinstance(log, dict) or not log:
        raise ValueError("NVMe sağlık günlüğü boş veya geçersiz; smartctl -j -a çıktısını kullanın.")
    out = dict(log)
    for key in COUNTERS:
        if key not in out or out[key] is None:
            out.pop(key, None)
            continue
        maximum = 255 if key in ("critical_warning", "percentage_used") else None
        if key in ("available_spare", "available_spare_threshold"):
            maximum = 100
        out[key] = _integer(out[key], key, maximum)
    if out.get("temperature") is not None:
        out["temperature"] = _temperature(out["temperature"], "temperature")
    if not any(out.get(key) is not None for key in (*REQUIRED, "temperature")):
        raise ValueError("NVMe günlüğünde değerlendirilebilir sağlık verisi yok.")
    return out


def score(disk: DiskInfo) -> Risk:
    """Return a conservative heuristic score, retaining missing-data warnings."""
    if not isinstance(disk, dict) or disk.get("kind") != "nvme":
        raise ValueError("NVMe değerlendirmesi için kind alanı 'nvme' olmalıdır.")
    log = _validated_log(disk.get("features"))
    temp = disk.get("temperature_c")
    if temp is None:
        temp = log.get("temperature")
    if temp is not None:
        temp = _temperature(temp)
    risk = 0.05
    drivers = ["Bu skor sezgisel NVMe kurallarına dayanır; arıza olasılığı değildir."]
    missing = [key for key in REQUIRED if log.get(key) is None]
    if temp is None:
        missing.append("temperature_c")
    if missing:
        risk = 0.35
        drivers.append("Eksik sağlık verisi nedeniyle değerlendirme sınırlı: " + ", ".join(missing))
    if log.get("critical_warning", 0):
        risk = max(risk, 0.90)
        drivers.append(f"Diskin kritik uyarı bayrağı açık (kod {log['critical_warning']}).")
    if log.get("media_errors", 0):
        risk = max(risk, 0.75)
        drivers.append(f"Medya / veri bütünlüğü hatası: {log['media_errors']}")
    spare, threshold = log.get("available_spare"), log.get("available_spare_threshold")
    if spare is not None:
        if threshold is not None and spare <= threshold:
            risk = max(risk, 0.85)
            drivers.append(f"Yedek alan eşikte veya altında: %{spare} (eşik %{threshold}).")
        elif spare < 50:
            risk = max(risk, 0.45)
            drivers.append(f"Yedek alan azalmış: %{spare}")
    used = log.get("percentage_used")
    if used is not None:
        if used >= 100:
            risk = max(risk, 0.70)
            drivers.append(f"Üreticinin öngördüğü yazma ömrüne ulaşıldı veya aşıldı: %{used}")
        elif used >= 80:
            risk = max(risk, 0.50)
            drivers.append(f"Yazma ömrünün çoğu kullanılmış: %{used}")
        else:
            risk = max(risk, used / 400)
    if temp is not None and temp >= 70:
        risk = max(risk, 0.35)
        drivers.append(f"Yüksek sıcaklık: {temp} °C")
    if len(drivers) == 1:
        drivers.append(f"Bildirilen sağlık alanlarında belirgin uyarı yok (ömür kullanımı %{used}).")
    return {"risk": round(risk, 2), "level": level_for(risk),
            "drivers": drivers, "method": "nvme_rules"}
