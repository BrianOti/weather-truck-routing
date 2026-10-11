
from risk_engine.checkpoints import WeatherCheckpoint


def generate_checkpoint_distances(
    total_distance_miles: float,
    interval_miles: int,
) -> list[float]:
    """Generate checkpoint distances, including the route's destination."""
    if total_distance_miles <= 0:
        raise ValueError("Total route distance must be greater than zero.")

    if interval_miles not in (10, 25, 50):
        raise ValueError("Interval must be 10, 25, or 50 miles.")

    distances = []
    distance = 0.0

    while distance < total_distance_miles:
        distances.append(distance)
        distance += interval_miles

    # Always include the destination, even if it isn't on an interval.
    if not distances or distances[-1] != total_distance_miles:
        distances.append(float(total_distance_miles))

    return distances