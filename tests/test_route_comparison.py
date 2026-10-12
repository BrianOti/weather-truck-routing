
import unittest

from risk_engine.route_summary import RouteSummary
from risk_engine.route_comparison import RouteOption, rank_routes


def make_route(route_id, severe, high, average, minutes):
    risk_miles = {
        "LOW": 0.0,
        "MODERATE": 0.0,
        "HIGH": float(high),
        "SEVERE": float(severe),
        "NO_TRAVEL": 0.0,
    }

    summary = RouteSummary(
        total_distance_miles=100.0,
        total_travel_minutes=minutes,
        risk_miles=risk_miles,
        average_risk=average,
    )

    return RouteOption(route_id=route_id, summary=summary)


class TestRouteComparison(unittest.TestCase):
    def test_fewest_severe_miles_wins_first(self):
        routes = [
            make_route("A", 10, 0, 0.5, 60),
            make_route("B", 5, 20, 2.0, 90),
        ]

        ranked = rank_routes(routes)

        self.assertEqual(ranked[0].route_id, "B")

    def test_high_miles_break_tie_on_severe_miles(self):
        routes = [
            make_route("A", 5, 20, 1.0, 60),
            make_route("B", 5, 10, 2.0, 90),
        ]

        ranked = rank_routes(routes)

        self.assertEqual(ranked[0].route_id, "B")

    def test_average_risk_breaks_tie_on_risk_miles(self):
        routes = [
            make_route("A", 5, 10, 1.5, 60),
            make_route("B", 5, 10, 1.0, 90),
        ]

        ranked = rank_routes(routes)

        self.assertEqual(ranked[0].route_id, "B")

    def test_travel_time_breaks_remaining_tie(self):
        routes = [
            make_route("A", 5, 10, 1.0, 90),
            make_route("B", 5, 10, 1.0, 60),
        ]

        ranked = rank_routes(routes)

        self.assertEqual(ranked[0].route_id, "B")

    def test_returns_all_routes_in_order(self):
        routes = [
            make_route("C", 10, 10, 2.0, 90),
            make_route("A", 0, 0, 0.5, 60),
            make_route("B", 5, 5, 1.0, 75),
        ]

        ranked = rank_routes(routes)

        self.assertEqual(
            [route.route_id for route in ranked],
            ["A", "B", "C"],
        )

    def test_rejects_empty_route_list(self):
        with self.assertRaises(ValueError):
            rank_routes([])

    def test_rejects_duplicate_route_ids(self):
        routes = [
            make_route("A", 0, 0, 0.5, 60),
            make_route("A", 5, 5, 1.0, 75),
        ]

        with self.assertRaises(ValueError):
            rank_routes(routes)


if __name__ == "__main__":
    unittest.main()