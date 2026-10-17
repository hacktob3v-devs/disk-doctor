"""Validate smartctl JSON and normalize ATA or NVMe health information."""
from core.contracts import DiskInfo
from core.nvme_rules import _integer, _temperature, _validated_log

ATA_IDS = (5, 9, 187, 188, 194, 197, 198)
CRITICAL_IDS = (5, 187, 188, 197, 198)


def _object(parent: dict, key: str) -> dict:
    value = parent.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"{key}: JSON nesnesi bekleniyor.")
    return value


def _text(value, field: str, default: str) -> str:
    if value is None or value == "":
        return default
    if not isinstance(value, str):
        raise ValueError(f"{field}: metin bekleniyor.")
    return value


def _validate_status(j: dict) -> None:
    """Reject explicit command failures and device-reported failed health."""
    command = _object(j, "smartctl")
    health = _object(j, "smart_status")
    status = command.get("exit_status", 0)
    if isinstance(status, bool) or not isinstance(status, int) or not 0 <= status <= 255:
        raise ValueError("smartctl.exit_status: 0–255 arası tam sayı bekleniyor.")
    if "passed" in health and not isinstance(health["passed"], bool):
        raise ValueError("smart_status.passed: true veya false bekleniyor.")
    if status & 7:
        raise ValueError("smartctl komutu veya disk verisini okuma başarısız; bağlantıyı ve erişim izinlerini kontrol edip çıktıyı yeniden alın.")
    if status & 8 or health.get("passed") is False:
        raise ValueError("Disk kendi S.M.A.R.T. sağlık testini geçemedi. Önemli verilerinizi hemen yedekleyin; bu çıktıdan sağlıklı model sonucu üretilemez.")


def parse(smartctl_json: dict) -> DiskInfo:
    """Convert supported smartctl schemas without inventing SMART counters."""
    j = smartctl_json
    if not isinstance(j, dict) or "device" not in j:
        raise ValueError("Bu dosya smartctl -j çıktısı değil (device alanı yok).")
    _validate_status(j)
    dev = _object(j, "device")
    protocol = _text(dev.get("protocol"), "device.protocol", "").lower()
    device_type = _text(dev.get("type"), "device.type", "").lower()
    has_nvme = "nvme_smart_health_information_log" in j
    has_ata = "ata_smart_attributes" in j
    if has_nvme and has_ata:
        raise ValueError("ATA ve NVMe sağlık alanları çelişkili; tek disk çıktısını kullanın.")
    if protocol == "nvme" or device_type == "nvme" or has_nvme:
        if (protocol and protocol != "nvme") or has_ata or device_type in ("ata", "sat", "sata"):
            raise ValueError("Disk protokolü ile NVMe sağlık günlüğü çelişkili.")
        kind = "nvme"
    elif protocol == "ata" or device_type in ("ata", "sat", "sata") or device_type.startswith("sat,") or has_ata:
        if protocol and protocol != "ata":
            raise ValueError("Disk protokolü ATA sağlık tablosuyla uyumlu değil.")
        kind = "ata"
    else:
        raise ValueError("Desteklenmeyen veya bilinmeyen disk protokolü; ATA/SATA veya NVMe çıktısı gerekli.")

    capacity_obj = _object(j, "user_capacity")
    capacity = capacity_obj.get("bytes")
    if capacity is None:
        capacity = j.get("nvme_total_capacity")
    capacity = _integer(capacity, "capacity_bytes") if capacity is not None else 0
    hours = _object(j, "power_on_time").get("hours")
    hours = _integer(hours, "power_on_time.hours") if hours is not None else None
    temp = _object(j, "temperature").get("current")
    temp = _temperature(temp, "temperature.current") if temp is not None else None

    if kind == "nvme":
        features = _validated_log(j.get("nvme_smart_health_information_log"))
        if hours is None:
            hours = features.get("power_on_hours")
        if temp is None:
            temp = features.get("temperature")
    else:
        table = _object(j, "ata_smart_attributes").get("table")
        if not isinstance(table, list) or not table:
            raise ValueError("ATA S.M.A.R.T. tablosu yok veya geçersiz; smartctl -j -a çıktısını kullanın.")
        features = {}
        seen = set()
        for attribute in table:
            if not isinstance(attribute, dict) or "id" not in attribute:
                raise ValueError("ATA S.M.A.R.T. satırı geçersiz; id alanı gerekli.")
            attr_id = _integer(attribute["id"], "ATA id", maximum=255, minimum=1)
            if attr_id in seen:
                raise ValueError(f"ATA S.M.A.R.T. tablosunda yinelenen id: {attr_id}")
            seen.add(attr_id)
            raw = _object(attribute, "raw").get("value")
            if raw is not None:
                raw = _integer(raw, f"smart_{attr_id}_raw")
            if attr_id in ATA_IDS and raw is not None:
                features[f"smart_{attr_id}_raw"] = raw
        if not any(f"smart_{i}_raw" in features for i in CRITICAL_IDS):
            raise ValueError("ATA tablosunda değerlendirilebilir kritik S.M.A.R.T. sayacı yok.")
        # Prefer decoded smartctl values over vendor-specific packed raw values.
        if hours is not None:
            features["smart_9_raw"] = hours
        else:
            hours = features.get("smart_9_raw")
        if temp is not None:
            features["smart_194_raw"] = temp
        elif "smart_194_raw" in features:
            raw_temp = features["smart_194_raw"]
            if raw_temp <= 200:
                temp = raw_temp
            else:
                features.pop("smart_194_raw")
    # The fixed contract uses 0 for unknown display-only hours/capacity;
    # health features remain absent so downstream evaluation can detect gaps.
    try:
        capacity_gb = round(capacity / 1e9, 1)
    except OverflowError as exc:
        raise ValueError("capacity_bytes: kapasite değeri çok büyük.") from exc
    return {"kind": kind,
            "model": _text(j.get("model_name") or j.get("model_family"), "model_name", "Bilinmeyen disk"),
            "serial": _text(j.get("serial_number"), "serial_number", "?"),
            "capacity_gb": capacity_gb, "power_on_hours": hours if hours is not None else 0,
            "temperature_c": temp, "features": features}
