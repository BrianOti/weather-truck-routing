
import unittest
from datetime import datetime

from risk_engine.checkpoints import WeatherCheckpoint
from risk_engine.route_summary import summarize_route


def make_checkpoint(distance, risk):
    return WeatherCheckpoint(
        distance_miles=distance,
        latitude=0.0,
        longitude=0.0,
        estimated_arrival=datetime(2026, 10, 12, 8, 0),
        wind_mph=0.0,
        rain_in_per_hour=0.0,
        snow_in_per_hour=0.0,
        risk_level=risk,
    )


class TestRouteSummary(unittest.TestCase):
    def test_calculates_miles_per_risk_level(self):
        checkpoints = [
            make_checkpoint(0, "LOW"),
            make_checkpoint(25, "HIGH"),
            make_checkpoint(50, "SEVERE"),
            make_checkpoint(60, "LOW"),
        ]

        summary = summarize_route(checkpoints, 60, 90)

        self.assertEqual(summary.risk_miles["LOW"], 25)
        self.assertEqual(summary.risk_miles["HIGH"], 25)
        self.assertEqual(summary.risk_miles["SEVERE"], 10)
        self.assertEqual(summary.risk_miles["MODERATE"], 0)
        self.assertEqual(summary.risk_miles["NO_TRAVEL"], 0)

    def test_calculates_weighted_average_risk(self):
        checkpoints = [
            make_checkpoint(0, "LOW"),
            make_checkpoint(25, "HIGH"),
            make_checkpoint(50, "SEVERE"),
            make_checkpoint(60, "LOW"),
        ]

        summary = summarize_route(checkpoints, 60, 90)

        expected = ((25 * 0) + (25 * 2) + (10 * 3)) / 60
        self.assertAlmostEqual(summary.average_risk, expected)

    def test_sorts_checkpoints_by_distance(self):
        checkpoints = [
            make_checkpoint(60, "LOW"),
            make_checkpoint(50, "SEVERE"),
            make_checkpoint(0, "LOW"),
            make_checkpoint(25, "HIGH"),
        ]

        summary = summarize_route(checkpoints, 60, 90)

        self.assertEqual(summary.risk_miles["HIGH"], 25)
        self.assertEqual(summary.risk_miles["SEVERE"], 10)

    def test_requires_starting_checkpoint(self):
        checkpoints = [
            make_checkpoint(10, "LOW"),
            make_checkpoint(60, "LOW"),
        ]

        with self.assertRaises(ValueError):
            summarize_route(checkpoints, 60, 90)

    def test_requires_destination_checkpoint(self):
        checkpoints = [
            make_checkpoint(0, "LOW"),
            make_checkpoint(50, "HIGH"),
        ]

        with self.assertRaises(ValueError):
            summarize_route(checkpoints, 60, 90)

    def test_requires_evaluated_checkpoints(self):
        checkpoints = [
            make_checkpoint(0, None),
            make_checkpoint(60, "LOW"),
        ]

        with self.assertRaises(ValueError):
            summarize_route(checkpoints, 60, 90)

    def test_rejects_duplicate_distances(self):
        checkpoints = [
            make_checkpoint(0, "LOW"),
            make_checkpoint(25, "HIGH"),
            make_checkpoint(25, "SEVERE"),
            make_checkpoint(60, "LOW"),
        ]

        with self.assertRaises(ValueError):
            summarize_route(checkpoints, 60, 90)


if __name__ == "__main__":
    unittest.main()