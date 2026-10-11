
from datetime import datetime, timedelta


def estimate_arrival_time(
    departure_time: datetime,
    distance_miles: float,
    total_distance_miles: float,
    total_travel_minutes: float,
) -> datetime:
    """Estimate arrival time using a constant average travel speed."""

    if total_distance_miles <= 0:
        raise ValueError("Total route distance must be greater than zero.")

    if distance_miles < 0 or distance_miles > total_distance_miles:
        raise ValueError(
            "Checkpoint distance must be within the route distance."
        )

    if total_travel_minutes < 0:
        raise ValueError("Travel time cannot be negative.")

    fraction_of_route = distance_miles / total_distance_miles

    elapsed_minutes = total_travel_minutes * fraction_of_route

    return departure_time + timedelta(minutes=elapsed_minutes)