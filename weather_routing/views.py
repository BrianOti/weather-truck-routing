import json
import math
import os
from datetime import datetime, timedelta

import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.middleware.csrf import get_token
from dotenv import load_dotenv

from risk_engine.checkpoints import WeatherCheckpoint, evaluate_checkpoint
from risk_engine.route_comparison import RouteOption, rank_routes
from risk_engine.route_geometry import generate_route_checkpoints
from risk_engine.route_summary import RouteSummary, summarize_route
from risk_engine.route_timing import estimate_arrival_time

load_dotenv()
HTTP = requests.Session()
HTTP.headers.update({"User-Agent": "WeatherAwareTruckRouting/1.0"})
TOMTOM_URL = "https://api.tomtom.com/routing/1/calculateRoute"
GEOCODE_URL = "https://api.tomtom.com/search/2/geocode"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
MILES_PER_METER = 1 / 1609.344
RISK_COLORS = {"LOW": "#19a974", "MODERATE": "#d9a514", "HIGH": "#ed7c28", "SEVERE": "#d84b4b", "NO_TRAVEL": "#772d91"}


def index(request):
    return render(request, "index.html", {"csrf_token": get_token(request)})


def _geocode(place, api_key):
    response = HTTP.get(f"{GEOCODE_URL}/{requests.utils.quote(place, safe='')}.json", params={"key": api_key, "limit": 1}, timeout=20)
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        raise ValueError(f"Could not find a location for “{place}”.")
    position = results[0]["position"]
    return {"latitude": position["lat"], "longitude": position["lon"], "label": results[0].get("address", {}).get("freeformAddress", place)}


def _routes(origin, destination, api_key):
    start = f"{origin['latitude']},{origin['longitude']}"
    end = f"{destination['latitude']},{destination['longitude']}"
    response = HTTP.get(f"{TOMTOM_URL}/{start}:{end}/json", params={"key": api_key, "maxAlternatives": 2, "routeType": "fastest", "traffic": "false", "travelMode": "truck", "routeRepresentation": "polyline"}, timeout=35)
    response.raise_for_status()
    routes = response.json().get("routes", [])
    if not routes:
        raise ValueError("The routing service did not return any route options.")
    return routes


def _weather(checkpoints, departure):
    # Open-Meteo accepts coordinate lists; batch all route checkpoints per trip.
    result = []
    for start in range(0, len(checkpoints), 20):
        group = checkpoints[start:start + 20]
        response = HTTP.get(WEATHER_URL, params={
            "latitude": ",".join(f"{point['latitude']:.5f}" for point in group),
            "longitude": ",".join(f"{point['longitude']:.5f}" for point in group),
            "hourly": "wind_speed_10m,rain,snowfall",
            "wind_speed_unit": "mph", "precipitation_unit": "inch",
            "forecast_days": 3, "timezone": "UTC",
        }, timeout=35)
        response.raise_for_status()
        data = response.json()
        locations = data if isinstance(data, list) else [data]
        for index, checkpoint in enumerate(group):
            forecast = locations[min(index, len(locations) - 1)]["hourly"]
            times = [datetime.fromisoformat(value) for value in forecast["time"]]
            eta = departure + timedelta(hours=checkpoint["offset_hours"])
            target = eta.replace(tzinfo=None)
            eta_slot = min(range(len(times)), key=lambda i: abs((times[i] - target).total_seconds()))
            series = []
            for hour in range(49):
                desired = times[eta_slot] + timedelta(hours=hour)
                slot = min(range(len(times)), key=lambda i: abs((times[i] - desired).total_seconds()))
                series.append({
                    "wind_mph": float(forecast["wind_speed_10m"][slot] or 0),
                    "rain_in_per_hour": float(forecast["rain"][slot] or 0),
                    "snow_in_per_hour": float(forecast["snowfall"][slot] or 0),
                    "forecast_time": times[slot].isoformat(),
                })
            result.append(series)
    return result


def _build_option(route, index, interval, departure, load):
    summary = route.get("summary", {})
    distance = summary.get("lengthInMeters", 0) * MILES_PER_METER
    minutes = summary.get("travelTimeInSeconds", 0) / 60
    points = [point for leg in route.get("legs", []) for point in leg.get("points", [])]
    if len(points) < 2 or distance <= 0:
        raise ValueError("A route did not include enough road geometry to create checkpoints.")
    coordinates = generate_route_checkpoints(points, distance, interval)
    for point in coordinates:
        point["offset_hours"] = (point["distance_miles"] / distance) * (minutes / 60)
    weather = _weather(coordinates, departure)
    checkpoints = []
    for point, hourly_conditions in zip(coordinates, weather):
        eta = estimate_arrival_time(departure, point["distance_miles"], distance, minutes)
        forecasts = []
        for conditions in hourly_conditions:
            checkpoint = WeatherCheckpoint(
                distance_miles=point["distance_miles"], latitude=point["latitude"], longitude=point["longitude"],
                estimated_arrival=eta, wind_mph=conditions["wind_mph"],
                rain_in_per_hour=conditions["rain_in_per_hour"], snow_in_per_hour=conditions["snow_in_per_hour"],
            )
            evaluate_checkpoint(checkpoint, load)
            forecasts.append({
                "risk": checkpoint.risk_level, "color": RISK_COLORS[checkpoint.risk_level],
                "wind_mph": round(checkpoint.wind_mph, 1), "rain_in_per_hour": round(checkpoint.rain_in_per_hour, 2),
                "snow_in_per_hour": round(checkpoint.snow_in_per_hour, 2), "forecast_time": conditions["forecast_time"],
            })
        conditions = hourly_conditions[0]
        checkpoint = WeatherCheckpoint(
            distance_miles=point["distance_miles"], latitude=point["latitude"], longitude=point["longitude"],
            estimated_arrival=eta, wind_mph=conditions["wind_mph"], rain_in_per_hour=conditions["rain_in_per_hour"],
            snow_in_per_hour=conditions["snow_in_per_hour"], risk_level=forecasts[0]["risk"],
        )
        checkpoints.append({
            "distance_miles": checkpoint.distance_miles, "latitude": checkpoint.latitude, "longitude": checkpoint.longitude,
            "eta": eta.isoformat(), "risk": checkpoint.risk_level, "color": RISK_COLORS[checkpoint.risk_level], "forecasts": forecasts,
            "wind_mph": round(checkpoint.wind_mph, 1), "rain_in_per_hour": round(checkpoint.rain_in_per_hour, 2),
            "snow_in_per_hour": round(checkpoint.snow_in_per_hour, 2),
        })
    result = summarize_route(checkpoints=[WeatherCheckpoint(
        distance_miles=item["distance_miles"], latitude=item["latitude"], longitude=item["longitude"],
        estimated_arrival=datetime.fromisoformat(item["eta"]), wind_mph=item["wind_mph"],
        rain_in_per_hour=item["rain_in_per_hour"], snow_in_per_hour=item["snow_in_per_hour"], risk_level=item["risk"],
    ) for item in checkpoints], total_distance_miles=distance, total_travel_minutes=minutes)
    return {
        "route_id": f"route-{index + 1}", "name": f"Route {index + 1}", "distance_miles": round(distance, 1),
        "travel_minutes": round(minutes), "checkpoints": checkpoints,
        "geometry": [{"latitude": p["latitude"], "longitude": p["longitude"]} for p in points],
        "summary": {"risk_miles": {key: round(value, 1) for key, value in result.risk_miles.items()}, "average_risk": round(result.average_risk, 2)},
    }


@require_POST
def plan_route(request):
    try:
        data = json.loads(request.body or "{}")
        origin_text, destination_text = str(data.get("origin", "")).strip(), str(data.get("destination", "")).strip()
        if not origin_text or not destination_text:
            return JsonResponse({"error": "Enter an origin and destination."}, status=400)
        try:
            interval = int(data.get("interval_miles", 25))
            load = float(data.get("load_lb", 0))
            departure = datetime.fromisoformat(str(data.get("departure_time", "")).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return JsonResponse({"error": "Enter a valid departure date/time, checkpoint interval, and load weight."}, status=400)
        if interval not in (10, 25, 50) or not math.isfinite(load) or load < 0:
            return JsonResponse({"error": "Choose a 10, 25, or 50 mile interval and a non-negative load."}, status=400)
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            return JsonResponse({"error": "TOMTOM_API_KEY is missing. Add it to the project .env file."}, status=503)
        origin, destination = _geocode(origin_text, api_key), _geocode(destination_text, api_key)
        raw_routes = _routes(origin, destination, api_key)
        routes = [_build_option(route, index, interval, departure, load) for index, route in enumerate(raw_routes)]
        options = [RouteOption(route_id=route["route_id"], summary=RouteSummary(
            total_distance_miles=route["distance_miles"], total_travel_minutes=route["travel_minutes"],
            risk_miles=route["summary"]["risk_miles"], average_risk=route["summary"]["average_risk"],
        )) for route in routes]
        ranked = rank_routes(options)
        routes.sort(key=lambda route: [item.route_id for item in ranked].index(route["route_id"]))
        routes[0]["recommended"] = True
        return JsonResponse({"origin": origin, "destination": destination, "routes": routes, "recommended_route_id": routes[0]["route_id"], "forecast_hours": 48})
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    except requests.RequestException as error:
        response = getattr(error, "response", None)
        if response is not None and response.status_code in (401, 403):
            message = "A routing or weather API rejected the request. Check the TomTom API key and access."
        else:
            message = "A routing or weather service is unavailable. Please try again shortly."
        return JsonResponse({"error": message}, status=502)
