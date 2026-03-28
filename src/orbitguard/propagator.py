from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
from sgp4.api import Satrec, jday

from .data_loader import TLEObject


@dataclass(slots=True)
class PropagationTrack:
    times: list[datetime]
    positions_km: np.ndarray
    velocities_kms: np.ndarray
    satrec: Satrec


def to_satrec(obj: TLEObject) -> Satrec:
    return Satrec.twoline2rv(obj.line1, obj.line2)


def tle_epoch_to_datetime(satrec: Satrec) -> datetime:
    year, month, day, hour, minute, second = satrec.epochyr, 1, 1, 0, 0, 0
    # epochyr iki hanelidir
    full_year = 2000 + year if year < 57 else 1900 + year
    base = datetime(full_year, 1, 1, tzinfo=timezone.utc)
    return base + timedelta(days=float(satrec.epochdays) - 1.0)


def propagate_object(
    obj: TLEObject,
    start_time: datetime | None = None,
    hours: int = 72,
    step_minutes: int = 10,
) -> PropagationTrack:
    satrec = to_satrec(obj)
    if start_time is None:
        start_time = datetime.now(timezone.utc)

    times: list[datetime] = []
    positions: list[np.ndarray] = []
    velocities: list[np.ndarray] = []

    steps = int((hours * 60) / step_minutes) + 1
    for step in range(steps):
        current = start_time + timedelta(minutes=step * step_minutes)
        jd, fr = jday(
            current.year,
            current.month,
            current.day,
            current.hour,
            current.minute,
            current.second + current.microsecond / 1_000_000.0,
        )
        error_code, r, v = satrec.sgp4(jd, fr)
        if error_code != 0:
            continue
        times.append(current)
        positions.append(np.array(r, dtype=float))
        velocities.append(np.array(v, dtype=float))

    if not positions:
        raise ValueError(f"Propagasyon başarısız: {obj.name}")

    return PropagationTrack(
        times=times,
        positions_km=np.vstack(positions),
        velocities_kms=np.vstack(velocities),
        satrec=satrec,
    )
