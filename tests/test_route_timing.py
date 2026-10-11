
import unittest
from datetime import datetime

from risk_engine.route_timing import estimate_arrival_time


class TestRouteTiming(unittest.TestCase):

    def setUp(self):
        self.departure = datetime(2026, 10, 12, 8, 0)

    def test_midpoint_arrival(self):
        arrival = estimate_arrival_time(
            departure_time=self.departure,
            distance_miles=60,
            total_distance_miles=120,
            total_travel_minutes=120,
        )

        self.assertEqual(arrival, datetime(2026, 10, 12, 9, 0))

    def test_departure_checkpoint(self):
        arrival = estimate_arrival_time(
            self.departure, 0, 120, 120
        )

        self.assertEqual(arrival, self.departure)

    def test_destination_arrival(self):
        arrival = estimate_arrival_time(
            self.departure, 120, 120, 120
        )

        self.assertEqual(arrival, datetime(2026, 10, 12, 10, 0))

    def test_checkpoint_cannot_exceed_route(self):
        with self.assertRaises(ValueError):
            estimate_arrival_time(
                self.departure, 130, 120, 120
            )

    def test_route_distance_must_be_positive(self):
        with self.assertRaises(ValueError):
            estimate_arrival_time(
                self.departure, 0, 0, 120
            )


if __name__ == "__main__":
    unittest.main()