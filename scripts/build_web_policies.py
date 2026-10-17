"""data/policies.json dosyasını web arayüzü için web/js/policies.js olarak yazar.

Kullanım: python scripts/build_web_policies.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "policies.json"
DST = ROOT / "web" / "js" / "policies.js"


def main() -> None:
    policies = json.loads(SRC.read_text(encoding="utf-8"))
    table = {
        p["id"]: {
            "category": p["category"],
            "title": p["title"],
            "text": p["text"],
            "keywords": p.get("keywords", []),
        }
        for p in policies
    }
    body = json.dumps(table, ensure_ascii=False, indent=2)
    DST.write_text(
        "// Otomatik üretildi: python scripts/build_web_policies.py\n"
        f"window.ED_POLICIES = {body};\n",
        encoding="utf-8",
    )
    print(f"{len(table)} politika -> {DST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
