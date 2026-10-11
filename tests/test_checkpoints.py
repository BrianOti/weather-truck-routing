
import unittest
from datetime import datetime

from risk_engine.classifier import RiskLevel
from risk_engine.checkpoints import (
    WeatherCheckpoint,
    evaluate_checkpoint,
)


class TestCheckpointEvaluation(unittest.TestCase):

    def test_checkpoint_receives_calculated_risk(self):
        checkpoint = WeatherCheckpoint(
            distance_miles=50,
            latitude=41.5,
            longitude=-87.5,
            estimated_arrival=datetime(2026, 10, 12, 9, 0),
            wind_mph=38,
            rain_in_per_hour=0.10,
            snow_in_per_hour=0,
        )

        result = evaluate_checkpoint(
            checkpoint=checkpoint,
            load_lb=20_000,
        )

        self.assertEqual(result.risk_level, "HIGH")
        self.assertIs(result, checkpoint)

    def test_heavy_load_can_make_wind_no_travel(self):
        checkpoint = WeatherCheckpoint(
            distance_miles=75,
            latitude=41.7,
            longitude=-87.3,
            estimated_arrival=datetime(2026, 10, 12, 9, 30),
            wind_mph=46,
            rain_in_per_hour=0,
            snow_in_per_hour=0,
        )

        result = evaluate_checkpoint(
            checkpoint=checkpoint,
            load_lb=35_000,
        )

        self.assertEqual(result.risk_level, "NO_TRAVEL")


if __name__ == "__main__":
    unittest.main()