
from enum import IntEnum


class RiskLevel(IntEnum):
    LOW = 0
    MODERATE = 1
    HIGH = 2
    SEVERE = 3
    NO_TRAVEL = 4


def classify_wind(wind_mph: float, load_lb: float) -> RiskLevel:
    """Classify wind risk using the assessment's wind and load rules."""

    if wind_mph >= 55:
        return RiskLevel.NO_TRAVEL

    if 45 <= wind_mph < 55 and load_lb > 30_000:
        return RiskLevel.NO_TRAVEL

    if 45 <= wind_mph < 55:
        return RiskLevel.SEVERE

    if 35 <= wind_mph < 45 and load_lb > 40_000:
        return RiskLevel.SEVERE

    if 35 <= wind_mph < 45:
        return RiskLevel.HIGH

    if 25 <= wind_mph < 35:
        return RiskLevel.MODERATE

    return RiskLevel.LOW


def classify_rain(rain_in_per_hour: float) -> RiskLevel:
    """Classify rainfall intensity using the assessment's thresholds."""

    if rain_in_per_hour > 1.00:
        return RiskLevel.NO_TRAVEL

    if rain_in_per_hour >= 0.50:
        return RiskLevel.SEVERE

    if rain_in_per_hour >= 0.25:
        return RiskLevel.HIGH

    if rain_in_per_hour >= 0.10:
        return RiskLevel.MODERATE

    return RiskLevel.LOW


def classify_snow(snow_in_per_hour: float) -> RiskLevel:
    """Classify snowfall intensity using the assessment's thresholds."""

    if snow_in_per_hour > 3.0:
        return RiskLevel.NO_TRAVEL

    if snow_in_per_hour >= 2.0:
        return RiskLevel.SEVERE

    if snow_in_per_hour >= 1.0:
        return RiskLevel.HIGH

    if snow_in_per_hour >= 0.5:
        return RiskLevel.MODERATE

    return RiskLevel.LOW


def classify_weather(
    wind_mph: float,
    rain_in_per_hour: float,
    snow_in_per_hour: float,
    load_lb: float,
) -> RiskLevel:
    """Return the highest risk across wind, rain, and snow."""

    risks = [
        classify_wind(wind_mph, load_lb),
        classify_rain(rain_in_per_hour),
        classify_snow(snow_in_per_hour),
    ]

    return max(risks)