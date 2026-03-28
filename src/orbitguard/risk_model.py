from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from .conjunction import ConjunctionEvent


@dataclass(slots=True)
class ModelBundle:
    model: RandomForestClassifier
    feature_names: list[str]


def _heuristic_label(
    miss_distance_km: float,
    relative_speed_kms: float,
    tle_age_hours: float,
    inc_gap_deg: float,
    mm_gap: float,
) -> int:
    score = 0
    if miss_distance_km < 5:
        score += 4
    elif miss_distance_km < 20:
        score += 3
    elif miss_distance_km < 50:
        score += 2
    elif miss_distance_km < 100:
        score += 1

    if relative_speed_kms > 12:
        score += 2
    elif relative_speed_kms > 8:
        score += 1

    if tle_age_hours > 48:
        score += 1

    if inc_gap_deg < 2.5:
        score += 1

    if mm_gap < 0.2:
        score += 1

    return 1 if score >= 5 else 0


def generate_synthetic_training_data(
    n_samples: int = 6000,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    rng = np.random.default_rng(random_state)

    miss_distance_km = np.exp(rng.uniform(np.log(0.5), np.log(200), size=n_samples))
    relative_speed_kms = rng.uniform(0.5, 15.0, size=n_samples)
    tle_age_hours = rng.uniform(1.0, 96.0, size=n_samples)
    object_tle_age_hours = rng.uniform(1.0, 96.0, size=n_samples)
    inc_gap_deg = rng.uniform(0.0, 25.0, size=n_samples)
    mean_motion_gap = rng.uniform(0.0, 3.0, size=n_samples)

    X = np.column_stack(
        [
            miss_distance_km,
            relative_speed_kms,
            tle_age_hours,
            object_tle_age_hours,
            inc_gap_deg,
            mean_motion_gap,
        ]
    )

    y = np.array(
        [
            _heuristic_label(md, rv, (ta + oa) / 2.0, ig, mm)
            for md, rv, ta, oa, ig, mm in X
        ],
        dtype=int,
    )

    feature_names = [
        "miss_distance_km",
        "relative_speed_kms",
        "target_tle_age_hours",
        "object_tle_age_hours",
        "inclination_gap_deg",
        "mean_motion_gap_rev_day",
    ]
    return X, y, feature_names


def fit_risk_model(random_state: int = 42) -> ModelBundle:
    X, y, feature_names = generate_synthetic_training_data(random_state=random_state)
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        random_state=random_state,
        class_weight="balanced",
        n_jobs=-1,
    )
    model.fit(X, y)
    return ModelBundle(model=model, feature_names=feature_names)


def features_from_event(event: ConjunctionEvent) -> np.ndarray:
    return np.array(
        [
            event.miss_distance_km,
            event.relative_speed_kms,
            event.target_tle_age_hours,
            event.object_tle_age_hours,
            event.inclination_gap_deg,
            event.mean_motion_gap_rev_day,
        ],
        dtype=float,
    )


def _physics_bonus(event: ConjunctionEvent) -> float:
    # Basit fiziksel sezgi: yakınlık ve hız tehlikeyi artırır.
    proximity = 1.0 / max(event.miss_distance_km, 1.0)
    speed = min(event.relative_speed_kms / 15.0, 1.0)
    age_penalty = min((event.target_tle_age_hours + event.object_tle_age_hours) / 200.0, 1.0)
    return 20.0 * proximity + 10.0 * speed + 5.0 * age_penalty


def score_events(events: list[ConjunctionEvent], model_bundle: ModelBundle) -> list[ConjunctionEvent]:
    if not events:
        return events

    X = np.vstack([features_from_event(event) for event in events])
    probabilities = model_bundle.model.predict_proba(X)[:, 1]

    scored: list[ConjunctionEvent] = []
    for event, prob in zip(events, probabilities):
        raw_score = 100.0 * float(prob) + _physics_bonus(event)
        event.risk_score = round(min(raw_score, 100.0), 2)
        scored.append(event)

    scored.sort(key=lambda x: x.risk_score, reverse=True)
    return scored
