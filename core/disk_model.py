"""Local ATA classifier. Scores are not calibrated shop failure probabilities."""
from __future__ import annotations

import os
import threading
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from core.contracts import DiskInfo, Risk, level_for

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_PATH = ROOT / "models" / "train_context.csv"
CRITICAL = {
    "smart_5_raw": "Yeniden atanmış sektör",
    "smart_187_raw": "Düzeltilemeyen hata",
    "smart_188_raw": "Komut zaman aşımı (üreticiye özgü ham sayaç)",
    "smart_197_raw": "Bekleyen (okunamayan) sektör",
    "smart_198_raw": "Çevrimdışı düzeltilemeyen sektör",
}
FEATURES = list(CRITICAL) + ["has_" + c.split("_")[1] for c in CRITICAL] + ["temp_c", "log_hours"]
_clf = None
_kind = None
_cache_key = None
_lock = threading.RLock()


def _col(df: pd.DataFrame, name: str) -> pd.Series:
    raw = df[name] if name in df else pd.Series(np.nan, index=df.index)
    values = pd.to_numeric(raw, errors="coerce").astype(float)
    return values.where(np.isfinite(values) & (values >= 0))


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Use the identical transform for context, holdout and live SMART data.

    Missing values stay NaN; the fitted pipeline imputes from training only and
    adds missingness indicators. Identifiers, dates and target never enter X.
    """
    out = pd.DataFrame(index=df.index)
    for col in CRITICAL:
        v = _col(df, col)
        out[col] = np.log1p(v)
        out["has_" + col.split("_")[1]] = (v > 0).astype(float).where(v.notna())
    t = _col(df, "smart_194_raw")
    out["temp_c"] = t.where(t.between(1, 99))
    out["log_hours"] = np.log1p(_col(df, "smart_9_raw"))
    return out[FEATURES]


def _pipeline(estimator):
    return Pipeline([
        ("missing", SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)),
        ("classifier", estimator),
    ])


def new_classifier(method: str | None = None):
    kind = method or os.getenv("DD_DISK_MODEL", "tabpfn")
    if kind not in {"tabpfn", "rf"}:
        raise ValueError("DD_DISK_MODEL yalnızca 'tabpfn' veya 'rf' olabilir.")
    if kind == "rf":
        estimator = RandomForestClassifier(
            n_estimators=300, min_samples_leaf=3, class_weight="balanced",
            random_state=42, n_jobs=2,
        )
    else:
        # Disable telemetry before importing the optional package. Inference
        # never auto-downloads checkpoints: provisioning is a separate action.
        os.environ["TABPFN_DISABLE_TELEMETRY"] = "1"
        checkpoint = Path(os.getenv("DD_TABPFN_PATH", str(ROOT / "models" / "tabpfn-v2-classifier.ckpt")))
        if not checkpoint.is_file():
            raise FileNotFoundError(f"Yerel TabPFN ağırlığı yok: {checkpoint}")
        from tabpfn import TabPFNClassifier
        estimator = TabPFNClassifier(
            device="cpu", model_path=str(checkpoint.resolve()), n_estimators=2,
            random_state=42, n_preprocessing_jobs=2,
        )
    return _pipeline(estimator), kind


def validate_context(ctx: pd.DataFrame) -> None:
    required = {"serial_number", "failure"}
    if not required.issubset(ctx):
        raise ValueError("Eğitim verisinde serial_number ve failure gerekli.")
    if ctx.empty or ctx.serial_number.isna().any() or ctx.serial_number.duplicated().any():
        raise ValueError("Eğitim verisi boş olamaz; her disk için tek, geçerli seri gerekli.")
    if set(pd.to_numeric(ctx.failure, errors="coerce").unique()) != {0, 1}:
        raise ValueError("Eğitim verisinde hem 0 hem 1 arıza sınıfı gerekli.")
    if make_features(ctx)[list(CRITICAL)].isna().all(axis=1).any():
        raise ValueError("Bazı eğitim disklerinde kritik SMART sayaçlarının tamamı eksik.")


def fit_on(ctx: pd.DataFrame, method: str | None = None, *, allow_fallback: bool = True):
    validate_context(ctx)
    requested = method or os.getenv("DD_DISK_MODEL", "tabpfn")
    if requested not in {"tabpfn", "rf"}:
        raise ValueError("DD_DISK_MODEL yalnızca 'tabpfn' veya 'rf' olabilir.")
    try:
        clf, kind = new_classifier(requested)
        clf.fit(make_features(ctx), ctx.failure.astype(int))
    except Exception as exc:
        if requested != "tabpfn" or not allow_fallback:
            raise
        warnings.warn(f"TabPFN kullanılamadı; gerçek RF yedeği kullanılıyor ({type(exc).__name__}: {exc}).", RuntimeWarning)
        clf, kind = new_classifier("rf")
        clf.fit(make_features(ctx), ctx.failure.astype(int))
    return clf, kind


def load_model():
    """Cache per context timestamp and model configuration, independent of cwd."""
    global _clf, _kind, _cache_key
    path = Path(os.getenv("DD_CONTEXT_PATH", str(CONTEXT_PATH))).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"{path} yok. Önce python -m scripts.train_disk_model çalıştırın.")
    stat = path.stat()
    key = (str(path), stat.st_mtime_ns, stat.st_size, os.getenv("DD_DISK_MODEL", "tabpfn"), os.getenv("DD_TABPFN_PATH", ""))
    with _lock:
        if _clf is None or key != _cache_key:
            clf, kind = fit_on(pd.read_csv(path))
            _clf, _kind, _cache_key = clf, kind, key
    return _clf, _kind


def drivers_for(features: dict) -> list[str]:
    drivers = []
    missing = []
    for col, label in CRITICAL.items():
        value = features.get(col)
        if value is None or pd.isna(value):
            missing.append(col)
        elif float(value) > 0:
            drivers.append(f"{label}: {int(value)}")
    if not drivers:
        drivers.append("Okunan kritik SMART sayaçlarında pozitif hata sayacı yok; bu sağlık garantisi değildir.")
    if missing:
        drivers.append("Eksik sayaçlar eğitim verisinden tahminle dolduruldu: " + ", ".join(missing))
    drivers.append("Model skoru; belirli bir sürede gerçek arıza olasılığı olarak kalibre edilmemiştir.")
    return drivers


def predict(disk: DiskInfo) -> Risk:
    if not isinstance(disk, dict) or disk.get("kind") != "ata":
        raise ValueError("Bu model yalnızca ATA diskler içindir; NVMe için nvme_rules.score kullanın.")
    features = disk.get("features")
    if not isinstance(features, dict):
        raise ValueError("Diskin SMART özellikleri eksik.")
    for col, value in features.items():
        if col in CRITICAL or col in {"smart_9_raw", "smart_194_raw"}:
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float, np.number)) or not np.isfinite(value) or value < 0):
                raise ValueError(f"Geçersiz SMART sayacı: {col}")
    x = make_features(pd.DataFrame([features]))
    if x[list(CRITICAL)].isna().all(axis=1).iloc[0]:
        raise ValueError("Risk hesabı için en az bir kritik ATA SMART sayacı gerekli.")
    clf, kind = load_model()
    positive = list(clf.classes_).index(1)
    score = float(clf.predict_proba(x)[0, positive])
    if not np.isfinite(score) or not 0 <= score <= 1:
        raise RuntimeError("Model geçerli bir skor üretmedi.")
    risk = round(score, 6)
    return {"risk": risk, "level": level_for(risk), "drivers": drivers_for(features), "method": kind}
