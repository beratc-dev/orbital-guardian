from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import pi

import numpy as np

from .data_loader import TLEObject
from .propagator import PropagationTrack, propagate_object, tle_epoch_to_datetime


@dataclass(slots=True)
class ConjunctionEvent:
    target_name: str
    object_name: str
    object_source: str
    tca_utc: str
    miss_distance_km: float
    relative_speed_kms: float
    target_tle_age_hours: float
    object_tle_age_hours: float
    inclination_gap_deg: float
    mean_motion_gap_rev_day: float
    risk_score: float = 0.0


def _inclination_deg(obj: TLEObject) -> float:
    from .propagator import to_satrec
    sat = to_satrec(obj)
    return float(sat.inclo * 180.0 / pi)


def _mean_motion_rev_day(obj: TLEObject) -> float:
    from .propagator import to_satrec
    sat = to_satrec(obj)
    return float(sat.no_kozai * 1440.0 / (2.0 * pi))


def prefilter_candidate(target: TLEObject, candidate: TLEObject) -> bool:
    inc_gap = abs(_inclination_deg(target) - _inclination_deg(candidate))
    mm_gap = abs(_mean_motion_rev_day(target) - _mean_motion_rev_day(candidate))
    return inc_gap <= 20.0 and mm_gap <= 2.0


def compute_conjunction_event(
    target: TLEObject,
    target_track: PropagationTrack,
    candidate: TLEObject,
    candidate_track: PropagationTrack,
) -> ConjunctionEvent:
    min_len = min(len(target_track.times), len(candidate_track.times))
    target_positions = target_track.positions_km[:min_len]
    candidate_positions = candidate_track.positions_km[:min_len]
    target_velocities = target_track.velocities_kms[:min_len]
    candidate_velocities = candidate_track.velocities_kms[:min_len]
    times = target_track.times[:min_len]

    relative_positions = target_positions - candidate_positions
    distances = np.linalg.norm(relative_positions, axis=1)
    best_idx = int(np.argmin(distances))

    relative_velocity = target_velocities[best_idx] - candidate_velocities[best_idx]
    relative_speed = float(np.linalg.norm(relative_velocity))

    now_utc = datetime.now(timezone.utc)
    target_epoch = tle_epoch_to_datetime(target_track.satrec)
    object_epoch = tle_epoch_to_datetime(candidate_track.satrec)

    return ConjunctionEvent(
        target_name=target.name,
        object_name=candidate.name,
        object_source=candidate.source,
        tca_utc=times[best_idx].isoformat(),
        miss_distance_km=float(distances[best_idx]),
        relative_speed_kms=relative_speed,
        target_tle_age_hours=max((now_utc - target_epoch).total_seconds() / 3600.0, 0.0),
        object_tle_age_hours=max((now_utc - object_epoch).total_seconds() / 3600.0, 0.0),
        inclination_gap_deg=abs(_inclination_deg(target) - _inclination_deg(candidate)),
        mean_motion_gap_rev_day=abs(_mean_motion_rev_day(target) - _mean_motion_rev_day(candidate)),
    )


def scan_conjunctions(
    targets: list[TLEObject],
    candidates: list[TLEObject],
    hours: int = 72,
    step_minutes: int = 10,
    top_k: int = 15,
) -> list[ConjunctionEvent]:
    target_tracks: dict[str, PropagationTrack] = {}
    for target in targets:
        target_tracks[target.name] = propagate_object(
            target,
            hours=hours,
            step_minutes=step_minutes,
        )

    events: list[ConjunctionEvent] = []
    for target in targets:
        target_track = target_tracks[target.name]
        for candidate in candidates:
            if candidate.name == target.name:
                continue
            if not prefilter_candidate(target, candidate):
                continue
            try:
                candidate_track = propagate_object(
                    candidate,
                    hours=hours,
                    step_minutes=step_minutes,
                )
                event = compute_conjunction_event(target, target_track, candidate, candidate_track)
            except Exception:
                continue

            # Ham filtre: çok uzak adayları rapora alma
            if event.miss_distance_km <= 200.0:
                events.append(event)

    # Önce ham yakınlığa göre sırala, sonra risk modeli bunu yeniden düzenleyecek.
    events.sort(key=lambda x: (x.miss_distance_km, -x.relative_speed_kms))
    return events[: max(top_k * 5, top_k)]


def event_to_dict(event: ConjunctionEvent) -> dict:
    return asdict(event)
