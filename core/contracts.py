"""Shared data types. Every module returns exactly these shapes.

Change this file only after agreeing at a team sync.
"""
from typing import Literal, Optional, TypedDict

Level = Literal["green", "yellow", "red"]
Urgency = Literal["dusuk", "orta", "yuksek"]
Likelihood = Literal["yuksek", "orta", "dusuk"]


class Part(TypedDict):
    parca: str
    olasilik: Likelihood
    neden: str


class Case(TypedDict):
    title: str
    url: str


class Triage(TypedDict):
    """triage.triage(complaint: str) -> Triage"""
    olasi_parcalar: list[Part]
    kontrol_adimlari: list[str]
    ek_sorular: list[str]
    aciliyet: Urgency
    veri_riski: bool
    benzer_vakalar: list[Case]
    sure_sn: float


class DiskInfo(TypedDict):
    """smart_parser.parse(smartctl_json: dict) -> DiskInfo"""
    kind: Literal["ata", "nvme"]
    model: str
    serial: str
    capacity_gb: float
    power_on_hours: int
    temperature_c: Optional[int]
    # ata:  {"smart_5_raw": .., "smart_9_raw": .., "smart_187_raw": .., "smart_188_raw": ..,
    #        "smart_194_raw": .., "smart_197_raw": .., "smart_198_raw": ..}
    # nvme: nvme_smart_health_information_log as given by smartctl
    features: dict


class Risk(TypedDict):
    """disk_model.predict(d) / nvme_rules.score(d) -> Risk"""
    risk: float          # 0.0 - 1.0
    level: Level
    drivers: list[str]   # e.g. ["Bekleyen sektör: 24"]
    method: Literal["tabpfn", "rf", "nvme_rules"]


GREEN_MAX = 0.30
YELLOW_MAX = 0.60


def level_for(risk: float) -> Level:
    if risk < GREEN_MAX:
        return "green"
    if risk < YELLOW_MAX:
        return "yellow"
    return "red"


# report.customer_report(shop: str, disk: DiskInfo, risk: Risk,
#                        triage: Triage | None) -> str  (Markdown)
