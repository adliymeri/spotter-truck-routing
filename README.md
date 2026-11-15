# Weather-Aware Truck Routing

A React + Django app that helps a truck driver pick the safest route, based on the weather forecast along each route, the load weight and the travel time.

## What it does

1. The user enters origin, destination, departure time, load weight and a weather check interval (10, 25 or 50 miles).
2. The app gets up to 3 routes.
3. It places checkpoints along each route and calculates when the truck reaches each one.
4. It checks the forecast at each checkpoint for that arrival time and scores the risk.
5. It recommends the best route.
6. The map shows all routes, checkpoints with weather details, route summaries and a weather heatmap with a 0–48 hour slider.

## Tech stack

- **Backend:** Python 3.13, Django, Django REST Framework, Redis
- **Frontend:** React, TypeScript, Vite, Material UI, MapLibre
- **APIs:** Mapbox (routing and address search), Open-Meteo (weather), OpenFreeMap (map tiles)

## How it works

### Risk rules

Each checkpoint takes the worst level of wind, rain and snow:

| Condition | Low | Moderate | High | Severe | No Travel |
|---|---|---|---|---|---|
| Wind (mph) | < 25 | 25–34 | 35–44 | 45–54 | ≥ 55 |
| Rain (in/hr) | < 0.10 | 0.10–0.25 | 0.25–0.50 | 0.50–1.00 | > 1.00 |
| Snow (in/hr) | < 0.5 | 0.5–1.0 | 1.0–2.0 | 2.0–3.0 | > 3.0 |

Load rules:
- 45–54 mph wind and over 30,000 lb → No Travel
- 35–44 mph wind and over 40,000 lb → Severe

### Checkpoints

- Checkpoints are placed every 10, 25 or 50 miles, plus the destination.
- Each checkpoint covers the road halfway to its neighbors, so the miles at each risk level add up to the route length.
- Arrival times come from the routing API's travel time for each road segment.

### Recommendation

Routes are sorted by:
1. Fewest No Travel miles
2. Fewest Severe miles
3. Fewest High miles
4. Lowest average risk
5. Shortest travel time

### Getting 3 routes

Mapbox returns up to 3 routes. If it returns fewer, the app asks for detour routes and keeps only those that are really different (less than 80% shared road). If no real third route exists, it shows 2.

### Heatmap

The backend creates a grid of up to 200 points within 25 miles of the routes and scores the risk at each point for every hour from 0 to 48. The frontend loads all hours once, so the slider is instant.

## Assumptions

- A value on a boundary belongs to the higher level (e.g. 35 mph wind is High).
- No Travel miles are ranked before Severe miles.
- Wind is the sustained wind, not gusts. Rain includes showers.
- Heatmap hour 0 is the departure time.
- Larger check intervals can miss short weather events between checkpoints.

## Limitations

- Open-Meteo's free plan has rate limits. Forecasts are cached for 1 hour to reduce calls.
- Truck restrictions only cover weight (no height or hazmat rules).
- Arrival times assume no rest breaks and no live traffic.
- Address search covers the US and Canada.

## Architecture

The backend keeps business logic separate from external services:

- `domain/`: risk rules, checkpoints, ranking and heatmap grid. Pure Python, fully tested.
- `ports.py`: interfaces for routing, weather and address search.
- `adapters/`: Mapbox and Open-Meteo implementations.
- `application/`: the use cases (`plan_trip`, `build_heatmap`).
- `api/`: endpoints, validation and error handling.

Changing a provider only means writing a new adapter.

## API

- `GET /api/geocode/?q=...`: address search
- `POST /api/plan/`: routes, checkpoints, risk and recommendation
- `POST /api/heatmap/`: hourly risk grid for the heatmap
- `GET /api/health/`: health check

## Run locally

You need Python 3.13, Node.js 22 and a free Mapbox token.

```bash
cp .env.example .env    # add your MAPBOX_TOKEN
```

Backend:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py runserver
```

Frontend (in a second terminal):
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Tests

```bash
cd backend
ruff check . && pytest -q
```

```bash
cd frontend
npm run lint && npm run build
```

## Deployment

Every push to `main` runs lint and tests. If they pass, GitHub Actions builds Docker images and deploys them to the server. If anything fails, nothing is deployed.
