
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

from risk_engine.route_geometry import generate_route_checkpoints

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("TOMTOM_API_KEY")

if not API_KEY:
    sys.exit("TOMTOM_API_KEY is missing. Check your root .env file.")

origin = "40.7128,-74.0060"
destination = "39.9526,-75.1652"
interval_miles = 25

url = (
    "https://api.tomtom.com/routing/1/calculateRoute/"
    f"{origin}:{destination}/json"
)

params = {
    "key": API_KEY,
    "maxAlternatives": 2,
    "routeType": "fastest",
    "traffic": "false",
    "travelMode": "car",
    "routeRepresentation": "polyline",
}

try:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

except requests.exceptions.HTTPError as error:
    status = error.response.status_code
    if status in (401, 403):
        sys.exit(
            f"TomTom rejected the request (HTTP {status}). "
            "Check your API key and routing access."
        )
    sys.exit(f"TomTom returned HTTP {status}.")

except requests.exceptions.RequestException as error:
    sys.exit(f"Could not reach TomTom: {error}")

routes = data.get("routes", [])

if not routes:
    sys.exit("TomTom returned no routes.")

print(f"Routes returned: {len(routes)}")

for index, route in enumerate(routes, start=1):
    summary = route.get("summary", {})
    distance_miles = summary.get("lengthInMeters", 0) / 1609.344
    travel_minutes = summary.get("travelTimeInSeconds", 0) / 60

    points = [
        point
        for leg in route.get("legs", [])
        for point in leg.get("points", [])
    ]

    print(f"\nRoute {index}")
    print(f"  Distance: {distance_miles:.1f} miles")
    print(f"  Travel time: {travel_minutes:.0f} minutes")
    print(f"  Geometry points: {len(points)}")

    if len(points) < 2:
        print("  Cannot generate checkpoints: insufficient geometry.")
        continue

    checkpoints = generate_route_checkpoints(
        points=points,
        route_distance_miles=distance_miles,
        interval_miles=interval_miles,
    )

    print(f"  Checkpoint interval: {interval_miles} miles")
    print(f"  Checkpoints generated: {len(checkpoints)}")

    for checkpoint in checkpoints:
        print(
            f"    Mile {checkpoint['distance_miles']:6.1f}: "
            f"({checkpoint['latitude']:.5f}, "
            f"{checkpoint['longitude']:.5f})"
        )