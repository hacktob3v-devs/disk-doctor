"""Gerçek modüllerle aynı imzalara sahip sahte fonksiyonlar.

Arayüz USE_MOCKS=1 iken bunları kullanır; böylece modeller hazır olmadan geliştirilebilir.
"""
import time
from typing import Optional

from core.contracts import DiskInfo, Risk, Triage, level_for

MODEL = "mock"


def warmup() -> bool:
    return True


def load_model():
    return None, "mock"


def triage(complaint: str) -> Triage:
    time.sleep(0.5)
    return {
        "olasi_parcalar": [
            {"parca": "Ekran kartı", "olasilik": "yuksek", "neden": "Fan dönüyor ama görüntü yok"},
            {"parca": "RAM", "olasilik": "orta", "neden": "POST aşamasında takılma olabilir"},
        ],
        "kontrol_adimlari": ["Harici monitör dene", "RAM'i çıkarıp tek modülle dene",
                             "Ekran kartını çıkarıp dahili grafikle dene"],
        "ek_sorular": ["Açılışta bip sesi var mı?", "Sorun ne zamandan beri var?"],
        "aciliyet": "orta",
        "veri_riski": False,
        "benzer_vakalar": [{"title": "PC turns on but no display", "url": "https://superuser.com/"}],
        "sure_sn": 0.5,
    }


def parse(smartctl_json: dict) -> DiskInfo:
    if "nvme_smart_health_information_log" in smartctl_json:
        return {"kind": "nvme", "model": "Mock NVMe 512GB", "serial": "MOCK-NVME",
                "capacity_gb": 512.0, "power_on_hours": 2300, "temperature_c": 41,
                "features": {"percentage_used": 7, "media_errors": 0}}
    return {"kind": "ata", "model": "WDC WD10EZEX", "serial": "MOCK-0001",
            "capacity_gb": 1000.0, "power_on_hours": 31000, "temperature_c": 38,
            "features": {"smart_5_raw": 112, "smart_197_raw": 24}}


def predict(disk: DiskInfo) -> Risk:
    risk = 0.82
    return {"risk": risk, "level": level_for(risk),
            "drivers": ["Bekleyen (okunamayan) sektör: 24", "Yeniden atanmış sektör: 112"],
            "method": "tabpfn"}


def score(disk: DiskInfo) -> Risk:
    return {"risk": 0.05, "level": "green",
            "drivers": ["Belirgin bir sorun yok (ömür kullanımı %7)"], "method": "nvme_rules"}


def customer_report(shop: str, disk: DiskInfo, risk: Risk, triage: Optional[Triage] = None) -> str:
    time.sleep(0.5)
    return (f"# {shop} — Disk Sağlık Raporu\n\n"
            f"**Disk:** {disk['model']} · **Arıza riski:** %{risk['risk'] * 100:.0f}\n\n"
            "## Diskinizin durumu\nDiskinizde arıza belirtileri var.\n\n"
            "## Önerimiz\n- Verilerinizi hemen yedekleyin.\n- Diskin değiştirilmesini öneririz.\n\n"
            "---\n_Bu rapor bir ön değerlendirmedir._")
