
import unittest

from risk_engine.classifier import (
    RiskLevel,
    classify_wind,
    classify_rain,
    classify_snow,
    classify_weather,
)


class TestWeatherClassifier(unittest.TestCase):

    def test_wind_thresholds(self):
        self.assertEqual(classify_wind(24.9, 10_000), RiskLevel.LOW)
        self.assertEqual(classify_wind(25, 10_000), RiskLevel.MODERATE)
        self.assertEqual(classify_wind(35, 10_000), RiskLevel.HIGH)
        self.assertEqual(classify_wind(45, 10_000), RiskLevel.SEVERE)
        self.assertEqual(classify_wind(55, 10_000), RiskLevel.NO_TRAVEL)

    def test_heavy_load_wind_rules(self):
        self.assertEqual(
            classify_wind(45, 30_001),
            RiskLevel.NO_TRAVEL,
        )
        self.assertEqual(
            classify_wind(35, 40_001),
            RiskLevel.SEVERE,
        )

    def test_rain_thresholds(self):
        self.assertEqual(classify_rain(0.09), RiskLevel.LOW)
        self.assertEqual(classify_rain(0.10), RiskLevel.MODERATE)
        self.assertEqual(classify_rain(0.25), RiskLevel.HIGH)
        self.assertEqual(classify_rain(0.50), RiskLevel.SEVERE)
        self.assertEqual(classify_rain(1.00), RiskLevel.SEVERE)
        self.assertEqual(classify_rain(1.01), RiskLevel.NO_TRAVEL)

    def test_snow_thresholds(self):
        self.assertEqual(classify_snow(0.49), RiskLevel.LOW)
        self.assertEqual(classify_snow(0.50), RiskLevel.MODERATE)
        self.assertEqual(classify_snow(1.00), RiskLevel.HIGH)
        self.assertEqual(classify_snow(2.00), RiskLevel.SEVERE)
        self.assertEqual(classify_snow(3.00), RiskLevel.SEVERE)
        self.assertEqual(classify_snow(3.01), RiskLevel.NO_TRAVEL)

    def test_highest_weather_risk_wins(self):
        result = classify_weather(
            wind_mph=20,
            rain_in_per_hour=0.10,
            snow_in_per_hour=2.5,
            load_lb=10_000,
        )

        self.assertEqual(result, RiskLevel.SEVERE)


if __name__ == "__main__":
    unittest.main()