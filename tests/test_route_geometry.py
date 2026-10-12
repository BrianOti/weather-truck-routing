
import unittest

from risk_engine.route_geometry import (
    generate_route_checkpoints,
    haversine_miles,
)


class TestRouteGeometry(unittest.TestCase):
    def setUp(self):
        # About 60 miles east along the equator.
        self.points = [
            {"latitude": 0.0, "longitude": 0.0},
            {"latitude": 0.0, "longitude": 0.5},
            {"latitude": 0.0, "longitude": 1.0},
        ]

        self.route_distance = haversine_miles(
            0.0, 0.0, 0.0, 1.0
        )

    def test_haversine_distance_is_positive(self):
        distance = haversine_miles(0, 0, 0, 1)
        self.assertGreater(distance, 69)

    def test_includes_origin_and_destination(self):
        checkpoints = generate_route_checkpoints(
            self.points, self.route_distance, 25
        )

        self.assertEqual(checkpoints[0]["distance_miles"], 0)
        self.assertEqual(
            checkpoints[-1]["distance_miles"],
            self.route_distance,
        )
        self.assertEqual(checkpoints[0]["longitude"], 0.0)
        self.assertEqual(checkpoints[-1]["longitude"], 1.0)

    def test_generates_regular_intervals(self):
        checkpoints = generate_route_checkpoints(
            self.points, self.route_distance, 25
        )

        distances = [
            checkpoint["distance_miles"]
            for checkpoint in checkpoints
        ]

        self.assertEqual(distances[0], 0)
        self.assertAlmostEqual(distances[1], 25)
        self.assertAlmostEqual(distances[2], 50)
        self.assertAlmostEqual(distances[-1], self.route_distance)

    def test_interpolates_checkpoint_coordinates(self):
        checkpoints = generate_route_checkpoints(
            self.points, self.route_distance, 25
        )

        # The 25-mile point should be between the first and second
        # geometry points on this straight synthetic route.
        self.assertGreater(checkpoints[1]["longitude"], 0)
        self.assertLess(checkpoints[1]["longitude"], 0.5)
        self.assertAlmostEqual(checkpoints[1]["latitude"], 0.0)

    def test_rejects_invalid_interval(self):
        with self.assertRaises(ValueError):
            generate_route_checkpoints(
                self.points, self.route_distance, 20
            )

    def test_rejects_insufficient_geometry(self):
        with self.assertRaises(ValueError):
            generate_route_checkpoints(
                self.points[:1], self.route_distance, 10
            )

    def test_rejects_zero_route_distance(self):
        with self.assertRaises(ValueError):
            generate_route_checkpoints(self.points, 0, 10)


if __name__ == "__main__":
    unittest.main()