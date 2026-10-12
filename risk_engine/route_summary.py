
from dataclasses import dataclass

from risk_engine.checkpoints import WeatherCheckpoint
from risk_engine.classifier import RiskLevel


@dataclass
class RouteSummary:
    total_distance_miles: float
    total_travel_minutes: float
    risk_miles: dict[str, float]
    average_risk: float


def summarize_route(
    checkpoints: list[WeatherCheckpoint],
    total_distance_miles: float,
    total_travel_minutes: float,
) -> RouteSummary:
    """Summarize route risk by assigning each checkpoint's risk to the
    road segment between that checkpoint and the next one.
    """
    if total_distance_miles <= 0:
        raise ValueError("Total route distance must be greater than zero.")

    if total_travel_minutes < 0:
        raise ValueError("Travel time cannot be negative.")

    if not checkpoints:
        raise ValueError("At least one checkpoint is required.")

    ordered = sorted(checkpoints, key=lambda cp: cp.distance_miles)

    # Require checkpoints to cover the entire route.
    if ordered[0].distance_miles != 0:
        raise ValueError("The first checkpoint must be at mile 0.")

    if ordered[-1].distance_miles != total_distance_miles:
        raise ValueError("The final checkpoint must be at the destination.")

    risk_miles = {level.name: 0.0 for level in RiskLevel}
    weighted_risk = 0.0

    for current, following in zip(ordered, ordered[1:]):
        segment_miles = following.distance_miles - current.distance_miles

        if segment_miles <= 0:
            raise ValueError("Checkpoint distances must be unique.")

        if current.risk_level is None:
            raise ValueError(
                f"Checkpoint at mile {current.distance_miles} "
                "has not been evaluated."
            )

        try:
            level = RiskLevel[current.risk_level]
        except KeyError as exc:
            raise ValueError(
                f"Unknown risk level: {current.risk_level}"
            ) from exc

        risk_miles[level.name] += segment_miles
        weighted_risk += int(level) * segment_miles

    average_risk = weighted_risk / total_distance_miles

    return RouteSummary(
        total_distance_miles=total_distance_miles,
        total_travel_minutes=total_travel_minutes,
        risk_miles=risk_miles,
        average_risk=average_risk,
    )