
from dataclasses import dataclass
from datetime import datetime

from risk_engine.classifier import classify_weather


@dataclass
class WeatherCheckpoint:
    distance_miles: float
    latitude: float
    longitude: float
    estimated_arrival: datetime
    wind_mph: float
    rain_in_per_hour: float
    snow_in_per_hour: float
    risk_level: str | None = None


def evaluate_checkpoint(
    checkpoint: WeatherCheckpoint,
    load_lb: float,
) -> WeatherCheckpoint:
    """Calculate and store the weather risk for a checkpoint."""

    risk = classify_weather(
        wind_mph=checkpoint.wind_mph,
        rain_in_per_hour=checkpoint.rain_in_per_hour,
        snow_in_per_hour=checkpoint.snow_in_per_hour,
        load_lb=load_lb,
    )

    checkpoint.risk_level = risk.name
    return checkpoint