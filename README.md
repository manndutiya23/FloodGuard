# FloodGuard 🌧️

**Hyperlocal Flood Intelligence for Mumbai**  
Amazon Environmental Hacks 2026 · Heat & Water track

> **Project status: Prototype in development.** This repository contains the project documentation and reference data while the application is being built. Features and AWS integrations described as planned are not yet claims of operational functionality.

## The problem

Heavy rainfall can cause highly localized waterlogging. City-wide weather information alone may not tell a commuter which areas have a history of flood exposure, whether a reported hotspot is recent, or which reports may deserve attention first.

FloodGuard aims to bring together historical ward-level vulnerability, suitable environmental data, geographic context, and time-stamped incident reports in one map-centred decision-support experience.

## What FloodGuard aims to do

- **Explore historical exposure:** Display ward-level historical exposure estimates with source attribution and clear caveats.
- **Understand risk:** Calculate an explainable heuristic assessment from available signals, showing the factors and data status behind it.
- **See incident reports:** Show submitted reports with timestamps and their actual verification/workflow status.
- **Prioritize attention:** Give responders a view of recent reports and locations that may warrant checking.
- **Communicate uncertainty:** Distinguish historical, observed, forecast, unavailable, stale, and simulated data wherever applicable.

These are the intended MVP capabilities. Check the implementation and demo before assuming a feature is available.

## How it is intended to work

1. Load the historical ward-exposure reference dataset.
2. Retrieve suitable rainfall observations or forecasts if a usable source is selected and integrated.
3. Collect and store incident reports, keeping unverified reports distinct from verified observations.
4. Calculate a transparent, rule-based risk assessment using only available inputs.
5. Display the map, explanations, timestamps, and report workflow through the web application.

A heuristic score is **not** a calibrated probability of flooding. The historical ward dataset is a background vulnerability reference, not live flood data or a current count of people in danger.

## Proposed technology and architecture

The current architecture plan proposes:

- **Frontend:** React with Vite; map-based interface.
- **API and processing:** Amazon API Gateway HTTP API and AWS Lambda.
- **Reference data:** CSV data, with Amazon S3 as a possible storage location.
- **Incident persistence:** Amazon DynamoDB if appropriate for the implemented workflow.
- **Operations:** Amazon CloudWatch for logs; EventBridge scheduling and SNS alerts only if their end-to-end workflows are implemented and tested.

This is a proposed architecture, not a statement that these services have already been deployed. The exact backend runtime and configuration will be finalized as implementation begins.

## Data and responsible use

The repository includes a historical Mumbai ward-exposure dataset transcribed from the Mumbai Climate Action Plan's *Climate & Air Pollution Risks and Vulnerability Assessment* report. The underlying population data is associated with Census 2011.

The source figures require verification against the report before exact values are treated as confirmed. They describe potential historical exposure using the source assessment's methodology; they do not establish current flood conditions or predict whether a flood will occur.

FloodGuard is a prototype for decision support, **not a replacement for official warnings or emergency services**. Reports may be unverified, and simulated data must be labelled. Missing or stale data must not silently be treated as zero rainfall or low risk.

## Repository structure

```text
FloodGuard/
├── frontend/                 # Web application (implementation in progress)
├── backend/                  # API and risk processing (implementation in progress)
├── data/
│   ├── reference/             # Historical reference dataset and its README
│   └── sample/                # Test/demo fixtures, clearly labelled
├── docs/
│   ├── PROJECT_BRIEF.md       # Product scope and project decisions
│   ├── ARCHITECTURE.md        # Proposed components and data flow
│   ├── DATA_SOURCES.md        # Data provenance and source status
│   ├── API_CONTRACT.md        # Proposed API request/response contract
│   ├── LIMITATIONS.md         # Known limitations and responsible-use rules
│   └── DEMO_SCRIPT.md         # Intentionally left empty until the app is ready
├── .env.example               # Safe configuration template; no secrets
├── .gitignore
└── README.md
```

## Getting started

**The application setup commands will be added after the frontend and backend scaffolds, package dependencies, and local run scripts are established and tested.** At this stage, the repository documents the intended system and holds the reference data; it is not yet a fully runnable application.

When implementation is available:

1. Clone the repository.
2. Install the dependencies for the relevant frontend and backend.
3. Copy the required settings from `.env.example` into a local environment file appropriate to that component.
4. Start the services using the verified project scripts.
5. Check the API health endpoint and test the main workflow with clearly labelled sample data.

Never commit local `.env` files, AWS credentials, API keys, access tokens, or real personal information.

## API plan

The proposed contract is documented in [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md). Planned endpoints include:

| Endpoint | Intended purpose |
|---|---|
| `GET /health` | API health check |
| `GET /wards` | Historical ward baseline |
| `GET /risk` | Risk assessment and explanations |
| `GET /reports` | Retrieve incident reports |
| `POST /reports` | Submit an incident report |
| `PATCH /reports/{id}` | Update report workflow status |

These endpoints are part of the agreed design; availability must be confirmed against the running implementation.

## Team workstreams

- **Mann:** Architecture, backend/AWS integration, API contract, and release coordination.
- **Manasvi:** Environmental data research, data processing, and risk-engine logic.
- **Laksh:** Geospatial frontend, map experience, and user interface.
- **Menaka:** Documentation and production of the YouTube demo video, including AI narration.

The team will work independently against shared contracts and integrate at planned checkpoints.

## Documentation

- [Project brief](docs/PROJECT_BRIEF.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Data sources](docs/DATA_SOURCES.md)
- [API contract](docs/API_CONTRACT.md)
- [Limitations and responsible use](docs/LIMITATIONS.md)

## Current priorities

1. Finalize shared contracts and local project scaffolds.
2. Build independently testable frontend, backend, and data/risk components.
3. Integrate the application locally and test failure/missing-data cases.
4. Connect the selected AWS services and verify the end-to-end workflow.
5. Record a demo that reflects the real application, clearly labelling any simulated inputs.

## License

No license has been specified yet. Unless a license is added, reuse and redistribution are not automatically granted.
