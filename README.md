# Weather-aware truck routing

A Django and React trip planner for comparing truck routes by forecast weather, cargo weight, and travel time. It uses TomTom for geocoding and alternate truck routes, and Open-Meteo for hourly weather forecasts. The risk thresholds and route ranking are implemented in `risk_engine/`.

## Run locally

1. Use Python 3.10 or newer and create a virtual environment.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Create a `.env` file in the project root (the same folder as `manage.py`) and put your TomTom API key in it:

   ```text
   TOMTOM_API_KEY=your_key
   ```

   The key needs TomTom Search and Routing API access. Open-Meteo is used for forecast data and does not need a key.

4. Start the app with `python manage.py runserver` and open `http://127.0.0.1:8000`.
5. To stop the server, press `Ctrl+C` in the terminal where it is running.

The planner geocodes the origin and destination, requests up to three truck routes, places weather checkpoints at the selected 10, 25, or 50 mile interval, and fetches hourly forecasts for those locations. At each checkpoint it uses the route ETA to select the forecast, applies the load-sensitive risk rules, and ranks routes by severe miles, high-risk miles, average risk, then travel time. The map uses MapLibre GL with OpenFreeMap vector tiles and lets you inspect checkpoint conditions through the next 48 forecast hours.

## Configuration

Set `DJANGO_SECRET_KEY` to a private random value and set `DJANGO_DEBUG=false` plus `DJANGO_ALLOWED_HOSTS` before exposing the app beyond a local development environment. React, MapLibre GL, and the map style currently load from public CDNs, so the browser needs internet access.

## Project layout

- `weather_routing/`: Django settings, routes, and API view.
- `templates/index.html` and `static/`: React interface and map.
- `risk_engine/`: reusable checkpoint, timing, risk, geometry, summary, and ranking logic.
- `tests/`: unit tests for the risk engine.
