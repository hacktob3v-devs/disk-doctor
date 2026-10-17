"""Fake implementations with the same signatures as the real modules.

The UI uses these while USE_MOCKS=1, so it can be built before the models are ready.
"""
from typing import Optional

from core.contracts import DiskInfo, Risk, Triage, level_for


def triage(complaint: str) -> Triage:
    return {
        "olasi_parcalar": [
            {"parca": "Ekran kartı", "olasilik": "yuksek", "neden": "Fan dönüyor ama görüntü yok"},
            {"parca": "RAM", "olasilik": "orta", "neden": "POST aşamasında takılma olabilir"},
        ],
        "kontrol_adimlari": ["Harici monitör dene", "RAM'i çıkarıp tek modülle dene"],
        "ek_sorular": ["Açılışta bip sesi var mı?", "Sorun ne zamandan beri var?"],
        "aciliyet": "orta",
        "veri_riski": False,
        "benzer_vakalar": [
            {"title": "PC turns on but no display", "url": "https://superuser.com/"},
        ],
        "sure_sn": 0.1,
    }


def parse(smartctl_json: dict) -> DiskInfo:
    return {
        "kind": "ata",
        "model": "WDC WD10EZEX",
        "serial": "MOCK-0001",
        "capacity_gb": 1000.0,
        "power_on_hours": 31000,
        "temperature_c": 38,
        "features": {"smart_5_raw": 112, "smart_197_raw": 24},
    }


def predict(disk: DiskInfo) -> Risk:
    risk = 0.82
    return {
        "risk": risk,
        "level": level_for(risk),
        "drivers": ["Bekleyen sektör: 24", "Yeniden atanmış sektör: 112"],
        "method": "tabpfn",
    }


def customer_report(shop: str, disk: DiskInfo, risk: Risk, triage: Optional[Triage] = None) -> str:
    return (
        f"# {shop} — Disk Sağlık Raporu\n\n"
        f"**Disk:** {disk['model']} ({disk['capacity_gb']:.0f} GB)\n\n"
        "Diskinizde arıza belirtileri var. Verilerinizi en kısa sürede yedeklemenizi öneririz.\n\n"
        "_Bu bir ön değerlendirmedir._"
    )
