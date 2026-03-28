from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import pandas as pd

from .conjunction import ConjunctionEvent


def write_reports(events: list[ConjunctionEvent], output_dir: Path) -> None:
    rows = [asdict(event) for event in events]
    df = pd.DataFrame(rows)

    csv_path = output_dir / "conjunction_events.csv"
    json_path = output_dir / "conjunction_events.json"
    summary_path = output_dir / "summary.txt"

    df.to_csv(csv_path, index=False)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    with summary_path.open("w", encoding="utf-8") as f:
        f.write("AETHRA – Orbital Guardian AI\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Toplam olay sayısı: {len(events)}\n")
        if events:
            f.write(f"En yüksek riskli olay: {events[0].target_name} vs {events[0].object_name}\n")
            f.write(f"Risk skoru: {events[0].risk_score}\n")
            f.write(f"TCA: {events[0].tca_utc}\n")
            f.write(f"Minimum mesafe (km): {events[0].miss_distance_km:.3f}\n")
            f.write(f"Göreli hız (km/s): {events[0].relative_speed_kms:.3f}\n")
