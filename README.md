# FloodGuard 🌧️

**Hyperlocal flood and waterlogging intelligence for Mumbai**  
Amazon Environmental Hacks 2026 · Heat & Water track

> **Current status: working prototype, not production-ready.** The deployed API and citizen report flow are operational. The photo upload → private S3 storage → report persistence path has been tested end to end. Responder authentication and protected responder-only access are not implemented yet.

## The problem

Heavy rainfall can cause highly localized waterlogging. City-wide weather information alone may not tell a commuter which areas have a history of flood exposure, whether a reported hotspot is recent, or which reports may deserve attention first.

FloodGuard brings together historical ward-level vulnerability, available environmental data, geographic context, and time-stamped citizen incident reports in a map-centred decision-support experience.

## Current capabilities

- **Ward exposure context:** historical Mumbai ward-level exposure reference data with provenance and caveats.
- **Environmental/risk endpoints:** weather-model data and an explainable, rule-based risk assessment; outputs must be interpreted with their source, freshness, geographic scope, and limitations.
- **Citizen reporting:** submit a report with location/category/details and optionally attach one JPEG, PNG, or WebP photo (maximum 5 MB).
- **Private photo storage:** the API issues a short-lived presigned S3 upload form; the bucket is private, and the API validates the uploaded object before linking it to a report.
- **Report workflow:** persisted reports have workflow and verification statuses; moving a report to `reviewed` does not itself verify the report.
- **Responder dashboard prototype:** review reports and update workflow status. **There is currently no responder sign-in or backend authorization boundary**, so this dashboard and status-update API must not be treated as secure operational access.

## Verified deployment slice

The following flow was exercised successfully against the deployed AWS-backed application:

1. The frontend requests photo-upload authorization from `POST /reports/photo-upload`.
2. The browser uploads the image directly to private S3 using the returned presigned form (successful S3 response: `204`).
3. The frontend submits `POST /reports` with the upload ID.
4. The backend validates the stored object and persists the report (successful creation response: `201`).

The deployed API also returned a healthy response from `GET /health`. These checks verify the tested path, not every possible failure mode or the production readiness of the system.

## Architecture

- **Frontend:** React, TypeScript, Vite.
- **API:** FastAPI/Python on AWS Lambda, fronted by Amazon API Gateway HTTP API.
- **Report persistence:** Amazon DynamoDB.
- **Photo evidence:** private Amazon S3 bucket, presigned POST upload, server-side object validation.
- **Environmental inputs:** Open-Meteo forecast/model data adapter.
- **Reference data and scoring:** historical ward exposure CSV and independently testable rule-based risk engine.

The deployment and implementation status is tracked in [Prototype status](docs/PROTOTYPE_STATUS.md). See [Architecture](docs/ARCHITECTURE.md) for component responsibilities and [API contract](docs/API_CONTRACT.md) for API semantics.

## Important limitations and responsible use

- FloodGuard is a prototype decision-support tool, **not an official flood warning system** and not a replacement for emergency services.
- A heuristic score is not a calibrated probability of flooding.
- Historical ward exposure is background vulnerability context, not live flood data or a current count of people in danger. The underlying population data is associated with Census 2011.
- A representative weather-model point is not independent weather data for every ward.
- Citizen reports may be unverified. Workflow status and verification status are separate.
- Photo objects remain private in S3, but **responder authentication and authorization are not yet implemented**. Do not use the current responder interface for sensitive operational access.
- Missing, stale, historical, forecast, and simulated data must remain distinguishable.

See [Limitations and responsible use](docs/LIMITATIONS.md) and [Data sources](docs/DATA_SOURCES.md).

## Getting started

### Frontend

From the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Configure the frontend's local environment using `frontend/.env.example`. To use the deployed API, set the documented API base URL and disable mock mode in your local environment. Do not commit `.env.local` or credentials.

### Backend (local development)

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app:app --reload
```

The local backend may require AWS configuration/environment variables to exercise DynamoDB and S3-backed report/photo endpoints. See [backend README](backend/README.md). Health check: `http://127.0.0.1:8000/health`; interactive API docs: `http://127.0.0.1:8000/docs`.

Never commit local environment files, AWS credentials, API keys, access tokens, presigned URLs, or real personal information.

## Key documentation

- [Prototype status and verified behavior](docs/PROTOTYPE_STATUS.md)
- [Project brief](docs/PROJECT_BRIEF.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Data sources](docs/DATA_SOURCES.md)
- [API contract](docs/API_CONTRACT.md)
- [Limitations and responsible use](docs/LIMITATIONS.md)
- [Demo script](docs/DEMO_SCRIPT.md)

## Team workstreams

- **Mann:** architecture, backend/AWS integration, API contract, infrastructure access, and release coordination.
- **Manasvi:** final sprint — deploy the frontend to a live HTTPS URL, connect it to the deployed API, verify production configuration, and document the deployment (3-hour cap).
- **Laksh:** final sprint — assess and, only if suitable labelled data exists, prototype a small explainable ML risk model against a baseline; preserve the heuristic fallback and document limitations (3-hour cap).
- **Menaka:** documentation and demo video production; update claims only after new functionality is verified.

The hard code-freeze deadline is **Sunday, 11 October 2026, 5:00 PM IST**. The remaining time until midnight is reserved for contingency, regression fixes, rehearsal, and demo/submission preparation—not new features. See [Final sprint plan and AWS access boundaries](docs/FINAL_SPRINT_PLAN.md) for owner deadlines, acceptance criteria, handoffs, and access notes.

## License

No license has been specified yet. Unless a license is added, reuse and redistribution are not automatically granted.
