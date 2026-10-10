# FloodGuard Frontend

React + Vite + TypeScript web app for FloodGuard: the flood intelligence map, citizen report form and responder dashboard. Styling uses Tailwind CSS; maps use Leaflet with OpenStreetMap tiles.

## Run locally

Requires Node.js 20 or newer.

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

Open http://localhost:5173.

### Mock mode vs live API

| `VITE_USE_MOCKS` | Behaviour |
|---|---|
| `true` (default) | Simulated data from `src/mocks/`. Every simulated item is labelled. Submitted reports live in memory and reset on reload. |
| `false` | Calls the API at `VITE_API_BASE_URL`. |

For the local FastAPI backend, keep `VITE_API_BASE_URL=/api`. The Vite dev server proxies `/api/*` to `VITE_API_PROXY_TARGET` (default `http://127.0.0.1:8000`), because the backend does not enable CORS yet. Start the backend first (see `backend/README.md`). Restart `npm run dev` after editing `.env.local`.

For a deployed API Gateway stage, set `VITE_API_BASE_URL` to its full URL. CORS must then be enabled on the API.

Never put secrets or AWS credentials in `VITE_` variables; they are bundled into browser code.

## Pages

- `/` — map with historical exposure, estimated risk and report layers; ward details and risk explanation. Supports deep links: `/?ward=F/N&layer=risk`.
- `/report` — citizen report form (map pin or device location, category, optional description).
- `/responder` — report queue with filters and workflow updates, plus calculated ward estimates.

## Structure

```text
src/
├── components/   Map, legend, risk panel, ward details, weather strip, report list, status states
├── pages/        Dashboard, ReportPage, ResponderDashboard
├── services/     api.ts — API client with mock switch and contract error handling
├── mocks/        wards.json (real reference CSV values) and simulated.ts (time-relative simulated data)
├── lib/          Ward boundary loading and lookup, formatting, colour scales
├── hooks/        useAsync data-loading hook
└── types/        Types matching docs/API_CONTRACT.md
```

## Data notes

- Ward boundaries are read from `data/reference/mumbai_ward_boundaries.geojson`, which stores positions as `[latitude, longitude]`. `src/lib/geo.ts` swaps them to GeoJSON's `[longitude, latitude]` at load time; the source file is not modified.
- A report's ward is matched by point-in-polygon against those boundaries. If the point is outside every ward, `ward_code` is left `null` rather than guessed.
- Scores are a heuristic index, not a flood probability. The UI shows reasons, data status, timestamps and the single-point weather limitation alongside every score.

## Not yet available on the backend

`GET/POST /reports` and `PATCH /reports/{id}` are not implemented in the API yet. In live mode, the report form and responder queue show a "not available on the API yet" message; use mock mode for those screens until they ship.

## Scripts

- `npm run dev` — development server
- `npm run build` — type-check and production build
- `npm run lint` — oxlint
