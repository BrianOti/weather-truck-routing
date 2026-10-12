from math import asin, cos, radians, sin, sqrt


EARTH_RADIUS_MILES = 3958.8


def haversine_miles(
    latitude1: float,
    longitude1: float,
    latitude2: float,
    longitude2: float,
) -> float:
    """Calculate the approximate great-circle distance between two points."""
    lat1, lon1, lat2, lon2 = map(
        radians,
        (latitude1, longitude1, latitude2, longitude2),
    )

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )

    # Protect against tiny floating-point rounding errors.
    a = min(1.0, max(0.0, a))

    return 2 * EARTH_RADIUS_MILES * asin(sqrt(a))


def generate_route_checkpoints(
    points: list[dict],
    route_distance_miles: float,
    interval_miles: int,
) -> list[dict]:
    """Place checkpoints along route geometry at regular mileage intervals.

    Each result contains distance_miles, latitude, and longitude.
    Mileage follows the routing API's reported route distance; coordinates
    are interpolated along the supplied geometry.
    """
    if len(points) < 2:
        raise ValueError("At least two geometry points are required.")

    if route_distance_miles <= 0:
        raise ValueError("Route distance must be greater than zero.")

    if interval_miles not in (10, 25, 50):
        raise ValueError("Interval must be 10, 25, or 50 miles.")

    # Calculate cumulative distance along the supplied geometry.
    cumulative = [0.0]

    for previous, current in zip(points, points[1:]):
        segment = haversine_miles(
            previous["latitude"],
            previous["longitude"],
            current["latitude"],
            current["longitude"],
        )
        cumulative.append(cumulative[-1] + segment)

    geometry_distance = cumulative[-1]

    if geometry_distance <= 0:
        raise ValueError("Geometry must cover a positive distance.")

    # Generate regular checkpoints and always include the destination.
    targets = []
    distance = 0.0

    while distance < route_distance_miles:
        targets.append(distance)
        distance += interval_miles

    targets.append(float(route_distance_miles))

    checkpoints = []

    for target in targets:
        # Scale API mileage to the measured geometry distance.
        geometry_target = (
            target / route_distance_miles
        ) * geometry_distance

        if target == 0:
            latitude = points[0]["latitude"]
            longitude = points[0]["longitude"]

        elif target == route_distance_miles:
            latitude = points[-1]["latitude"]
            longitude = points[-1]["longitude"]

        else:
            for index in range(1, len(points)):
                if cumulative[index] >= geometry_target:
                    segment_start = cumulative[index - 1]
                    segment_end = cumulative[index]
                    segment_length = segment_end - segment_start

                    if segment_length == 0:
                        fraction = 0.0
                    else:
                        fraction = (
                            geometry_target - segment_start
                        ) / segment_length

                    previous = points[index - 1]
                    current = points[index]

                    latitude = previous["latitude"] + fraction * (
                        current["latitude"] - previous["latitude"]
                    )
                    longitude = previous["longitude"] + fraction * (
                        current["longitude"] - previous["longitude"]
                    )
                    break
            else:
                raise ValueError("Could not locate checkpoint on geometry.")

        checkpoints.append({
            "distance_miles": target,
            "latitude": latitude,
            "longitude": longitude,
        })

    return checkpoints