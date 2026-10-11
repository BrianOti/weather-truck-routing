
import unittest

from risk_engine.checkpoint_generator import generate_checkpoint_distances


class TestCheckpointGenerator(unittest.TestCase):
    def test_25_mile_interval(self):
        self.assertEqual(
            generate_checkpoint_distances(60, 25),
            [0.0, 25.0, 50.0, 60.0],
        )

    def test_route_shorter_than_interval(self):
        self.assertEqual(
            generate_checkpoint_distances(8, 10),
            [0.0, 8.0],
        )

    def test_exact_interval(self):
        self.assertEqual(
            generate_checkpoint_distances(50, 25),
            [0.0, 25.0, 50.0],
        )

    def test_supported_intervals(self):
        for interval in (10, 25, 50):
            with self.subTest(interval=interval):
                distances = generate_checkpoint_distances(100, interval)
                self.assertEqual(distances[0], 0.0)
                self.assertEqual(distances[-1], 100.0)

    def test_invalid_interval(self):
        with self.assertRaises(ValueError):
            generate_checkpoint_distances(60, 20)

    def test_invalid_route_distance(self):
        with self.assertRaises(ValueError):
            generate_checkpoint_distances(0, 10)


if __name__ == "__main__":
    unittest.main()