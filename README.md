# Aircraft Data Link Optimizer

A research/prototype tool to visualize aircraft and compute line-of-sight (LOS) relay chains between two aircraft over a region. The application loads aircraft state, forecasts short-term positions, constructs a visibility graph, and finds relay paths (start → end) using intermediate aircraft as relays. This README explains the architecture, design decisions, and how to run and extend the system.

---
## Video Demo
https://drive.google.com/file/d/1ADWGopXJoTzlVtRBbmE5-FsWlsVMGsDo/view?usp=sharing
## Quick summary

What this does
- Visualize aircraft positions on an interactive map.
- Select a start and an end aircraft by clicking markers.
- Forecast positions for a short horizon (seconds) using constant-velocity extrapolation.
- Build a visibility graph using pairwise LOS tests and compute a relay chain between start and end.
- Uses the OpenSky Network API as the authoritative aircraft state source (see credential requirement below).

Primary code locations
- `src/map_GUI.py` — Dash application and interactive UI (map, controls, callbacks).
- `src/update_planes.py` — ingestion and normalization of aircraft state.
- `src/calculate_path.py` — forecasting, LOS predicates, and path-finding logic.
- `src/main.py` — small launcher/entrypoint.

Important operational note
- The application requires an OpenSky API credential. A credential file must be present in the main project folder (root of the repository) for the app to connect to OpenSky. Place your credential file there as required by the code (e.g., `credentials.json` or the filename expected by `src/update_planes.py`). Do not commit shared or production credentials to public repositories.

---

## High-level architecture

The system is organized into three logical layers:

1. Presentation (UI)
   - Implemented in `src/map_GUI.py`.
   - Dash + Plotly map visualization provides markers for aircraft, colored start/end markers, and polyline overlays for computed paths.
   - UI controls: Update Positions, Select Start, Select End, Forecast slider, Calculate.
   - Selection persistence uses aircraft `icao24` identifiers to survive dataset refreshes.

2. Data ingestion & normalization
   - Implemented in `src/update_planes.py`.
   - Responsible for contacting the OpenSky API (using credentials stored in the repository root), reading raw state vectors, and normalizing them into consistent plane dictionaries with keys such as `icao24`, `callsign`, `lat`, `lon`, `geo_alt`, `velocity`, `track`.
   - Optional snapshotting can be added to persist exact states for reproducible experiments.

3. Computation & path finding
   - Implemented in `src/calculate_path.py`.
   - Forecasting: `extrapolate_position(lat, lon, velocity, track, seconds)` — predicts future position using geodesic movement given velocity and bearing.
   - LOS predicate: `los_test(a, b)` — evaluates geometric LOS between two aircraft given positions and altitudes (current implementation is geometric and does not account for terrain).
   - Path search: `compute_los_path(planes_list, start_icao, end_icao, forecast_seconds=0)` — constructs a visibility graph and finds an optimal relay chain. Uses 2 different cost metrics to determine lowest latency:
     - Hop-minimizing (BFS / unit edge weight).
     - Distance- or latency-minimizing (Dijkstra with 3D distance or distance/velocity as edge weight).

Data flow (typical)
Client (browser) → Dash server (`src/map_GUI.py`) → `update_planes.get_planes()` → normalized `planes_list` → (optional) `extrapolate_position()` → graph construction (`compute_los_path()`) → path result → UI renders overlay.

---

## Key design decisions & rationale

- Identity by ICAO (`icao24`):
  - Ensures UI selection persistence across refreshes and avoids brittle index-based selection.

- Kinematic forecasting (constant velocity + track):
  - Simple and computationally cheap. Suitable for short-term forecasts used in visualization and path planning.
  - More advanced models (turn rates, Kalman filters, wind effects) are possible future upgrades.

- Geometric LOS model:
  - Fast and deterministic; ignores terrain and propagation effects initially to keep computation tractable and explainable.
  - Clear path for enhancement: integrate DEM/SRTM for horizon blocking and Fresnel zone checks for radio propagation.

- Graph construction approach:
  - Current naive pairwise LOS checks (O(N^2)) are simple and effective for moderate N.
  - For larger numbers of aircraft, spatial indexing (R-tree, k-d tree) or radius-based culling is recommended to reduce candidate pairs.

- UI stack:
  - Dash/Plotly for rapid interactive prototyping and single-user visualization. If the application needs to scale to many concurrent users, consider splitting into a backend API and a dedicated web front-end.

---

## Algorithms, complexity & optimisation

- Forecasting: O(N) — each plane is extrapolated independently.
- Graph construction: O(N^2) naive — pairwise LOS checks for N aircraft.
  - Optimization strategies:
    - Spatial culling: quick coordinate bounding checks, nearest-neighbor search, or a fixed radius threshold before exact LOS tests.
    - Vectorization: use NumPy to batch distance/bearing calculations.
    - Indexing: use an R-tree (rtree, pygeos) to query neighbors within a radius.

- Path-finding:
  - BFS for hop-minimizing: O(N + E).
  - Dijkstra for weighted shortest paths: O((N + E) log N).

- Edge-weight design:
  - Hop count (1 per edge) minimizes number of relays.
  - 3D Euclidean distance or distance/velocity minimize link length or estimated latency.

---

## Practical implementation notes

- Geodesic math:
  - Use geopy or pyproj for accurate movement on the ellipsoid; avoid planar approximations for non-trivial distances.
  - Ensure consistent units (velocity in m/s) before computing travel distance = velocity * seconds.

- Modular LOS:
  - Implement `los_test` as a plug-in point so higher-fidelity models (terrain-aware, Fresnel zone) can be introduced without changing the graph pipeline.

- Server-side computation:
  - Keep heavy computations on the server; transmit compact results (ordered list of ICAO nodes and polylines) to the client for rendering.

- Credentials:
  - The app expects OpenSky API credentials to be available in the repository main folder. Confirm the exact filename and format required by `src/update_planes.py` and document it in code comments.
  - For security, prefer not to commit production credentials in public repositories. If credentials are committed for development, ensure the repository access policy is controlled.

---

## Limitations & roadmap

Planned / recommended improvements
- Terrain-aware LOS: integrate Digital Elevation Models (SRTM) for horizon blocking.
- Radio propagation: implement Fresnel zone and frequency-dependent link budgets.
- Spatial indexing and vectorized math to scale graph construction efficiently.
- More realistic motion models: include turn rate, acceleration, or Kalman filtering for smoother forecasts. Can also include flight plan.
- Headless API mode for batch experiments and automated routing tests.
- Tests: add unit tests for extrapolation, LOS checks, and path search; add CI.

---

## Project layout (actual)

Repository root
- `.gitignore`
- `README.md` (this file)
- `.idea/`

`src/`
- `map_GUI.py` — Dash app (UI + callbacks).
- `update_planes.py` — OpenSky ingestion and normalization (reads credential file from repository root).
- `calculate_path.py` — extrapolate/LOS/path algorithms.
- `main.py` — launcher/entrypoint.

`tests/`
- Directory present for unit tests and additional tooling.

---

## Running the app

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies (adjust to your `requirements.txt` if present):
```bash
pip install dash plotly requests geopy numpy
# add networkx or scipy if using graph utilities
```

3. Ensure OpenSky credentials are placed in the repository root in the filename expected by `src/update_planes.py` (e.g., `credentials.json`).

4. Start the UI:
```bash
python src/map_GUI.py
# open http://127.0.0.1:8050
```

5. In the UI:
- Click "Update Positions" to fetch current aircraft states from OpenSky.
- Click "Select Start" and "Select End" to choose endpoints.
- Adjust Forecast slider and click "Calculate" to compute the LOS relay chain.

---
