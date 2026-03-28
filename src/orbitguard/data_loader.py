from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import time

import requests


BASE_URL = "https://celestrak.org/NORAD/elements/gp.php"
REQUEST_TIMEOUT = 30

# CelesTrak açık debris grupları.
DEBRIS_GROUPS = [
    "cosmos-1408-debris",
    "fengyun-1c-debris",
    "iridium-33-debris",
    "cosmos-2251-debris",
]


@dataclass(slots=True)
class TLEObject:
    name: str
    line1: str
    line2: str
    source: str


def _request(params: dict[str, str]) -> str:
    response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    text = response.text.strip()
    if not text:
        raise ValueError(f"Boş cevap döndü: {params}")
    return text


def parse_tle_text(text: str, source: str) -> list[TLEObject]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    objects: list[TLEObject] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("1 ") and i + 1 < len(lines) and lines[i + 1].startswith("2 "):
            name = f"UNKNOWN_{i}"
            line1 = lines[i]
            line2 = lines[i + 1]
            objects.append(TLEObject(name=name, line1=line1, line2=line2, source=source))
            i += 2
            continue

        if i + 2 < len(lines) and lines[i + 1].startswith("1 ") and lines[i + 2].startswith("2 "):
            name = line
            line1 = lines[i + 1]
            line2 = lines[i + 2]
            objects.append(TLEObject(name=name, line1=line1, line2=line2, source=source))
            i += 3
            continue

        i += 1

    return objects


def deduplicate(objects: Iterable[TLEObject]) -> list[TLEObject]:
    seen: set[tuple[str, str]] = set()
    unique: list[TLEObject] = []
    for obj in objects:
        key = (obj.line1, obj.line2)
        if key in seen:
            continue
        seen.add(key)
        unique.append(obj)
    return unique


def fetch_group_tles(group: str) -> list[TLEObject]:
    text = _request({"GROUP": group, "FORMAT": "tle"})
    return parse_tle_text(text, source=f"group:{group}")


def fetch_name_tles(name: str) -> list[TLEObject]:
    text = _request({"NAME": name, "FORMAT": "tle"})
    return parse_tle_text(text, source=f"name:{name}")


def best_name_match(query: str, candidates: list[TLEObject]) -> TLEObject | None:
    query_upper = query.strip().upper()
    exact = [obj for obj in candidates if obj.name.upper() == query_upper]
    if exact:
        return exact[0]

    starts = [obj for obj in candidates if obj.name.upper().startswith(query_upper)]
    if starts:
        return starts[0]

    contains = [obj for obj in candidates if query_upper in obj.name.upper()]
    if contains:
        return contains[0]

    return candidates[0] if candidates else None


def load_targets_by_name(target_names: list[str]) -> list[TLEObject]:
    targets: list[TLEObject] = []
    for name in target_names:
        # CelesTrak'ı gereksiz zorlamamak için küçük gecikme
        time.sleep(0.2)
        candidates = fetch_name_tles(name)
        best = best_name_match(name, candidates)
        if best is not None:
            targets.append(best)
    return deduplicate(targets)


def load_debris_catalog(
    debris_groups: list[str],
    max_per_group: int = 150,
) -> list[TLEObject]:
    debris: list[TLEObject] = []
    for group in debris_groups:
        time.sleep(0.2)
        try:
            group_objects = fetch_group_tles(group)
        except Exception:
            continue
        debris.extend(group_objects[:max_per_group])
    return deduplicate(debris)
