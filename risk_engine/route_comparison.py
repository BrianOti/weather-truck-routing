
from dataclasses import dataclass

from risk_engine.route_summary import RouteSummary


@dataclass
class RouteOption:
    route_id: str
    summary: RouteSummary


def rank_routes(routes: list[RouteOption]) -> list[RouteOption]:
    """Rank routes using the assessment's risk and travel-time priorities."""
    if not routes:
        raise ValueError("At least one route is required.")

    route_ids = [route.route_id for route in routes]
    if len(route_ids) != len(set(route_ids)):
        raise ValueError("Route IDs must be unique.")

    return sorted(
        routes,
        key=lambda route: (
            route.summary.risk_miles["SEVERE"],
            route.summary.risk_miles["HIGH"],
            route.summary.average_risk,
            route.summary.total_travel_minutes,
        ),
    )