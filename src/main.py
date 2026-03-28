from __future__ import annotations

import argparse
from pathlib import Path

from src.orbitguard.data_loader import DEBRIS_GROUPS, load_targets_by_name, load_debris_catalog
from src.orbitguard.conjunction import scan_conjunctions
from src.orbitguard.risk_model import fit_risk_model, score_events
from src.orbitguard.report import write_reports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AETHRA – Orbital Guardian AI")
    parser.add_argument(
        "--targets",
        nargs="+",
        required=True,
        help="Hedef uydu adları. Örnek: --targets 'TURKSAT 5A' 'GOKTURK-1'",
    )
    parser.add_argument("--hours", type=int, default=72, help="Analiz ufku (saat)")
    parser.add_argument("--step-minutes", type=int, default=10, help="Zaman adımı (dakika)")
    parser.add_argument("--top-k", type=int, default=15, help="En yüksek riskli olay sayısı")
    parser.add_argument(
        "--max-debris-per-group",
        type=int,
        default=150,
        help="Her debris grubu için alınacak maksimum nesne sayısı",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("[1/5] Hedef uydular yükleniyor...")
    targets = load_targets_by_name(args.targets)
    if not targets:
        raise SystemExit("Hiç hedef uydu bulunamadı. İsimleri kontrol et.")

    print("[2/5] Debris katalogları yükleniyor...")
    debris_objects = load_debris_catalog(
        debris_groups=DEBRIS_GROUPS,
        max_per_group=args.max_debris_per_group,
    )
    if not debris_objects:
        raise SystemExit("Debris kataloğu boş döndü. İnternet bağlantısını ve grup sorgularını kontrol et.")

    print("[3/5] Yakınlaşma analizi çalışıyor...")
    events = scan_conjunctions(
        targets=targets,
        candidates=debris_objects,
        hours=args.hours,
        step_minutes=args.step_minutes,
        top_k=args.top_k,
    )
    if not events:
        raise SystemExit("Herhangi bir yakınlaşma olayı bulunamadı.")

    print("[4/5] Risk modeli eğitiliyor ve olaylar puanlanıyor...")
    model_bundle = fit_risk_model(random_state=42)
    scored_events = score_events(events, model_bundle=model_bundle)

    print("[5/5] Raporlar yazılıyor...")
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    write_reports(scored_events, output_dir=output_dir)

    print("\nTamamlandı.")
    print(f"Toplam olay: {len(scored_events)}")
    print(f"CSV: {output_dir / 'conjunction_events.csv'}")
    print(f"JSON: {output_dir / 'conjunction_events.json'}")
    print(f"Özet: {output_dir / 'summary.txt'}")


if __name__ == "__main__":
    main()
