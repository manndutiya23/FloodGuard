# FloodGuard System Architecture

**Project:** FloodGuard — Mumbai Hyperlocal Flood Intelligence  
**Status:** Proposed architecture — implementation in progress  
**Version:** 1.1

## 1. Purpose

This document describes the planned system components, their responsibilities, and how data moves through FloodGuard. It is an implementation guide, not a claim that every component is already deployed.

The MVP combines a historical ward-level exposure baseline with available weather-model data and citizen incident reports to produce an explainable, explicitly qualified risk assessment.

## 2. Architecture at a glance

```text
                    Open-Meteo Forecast API
                              |
                              v
                    Python data adapter
              fetch -> validate -> normalize
                              |
                              v
Historical ward CSV ---> Risk engine <--- Incident reports
                              |
                              v
                       FloodGuard API
                              |
                              v
                      React / Vite UI
                ward view, map, explanations
```

Planned AWS deployment:

```text
React / Vite frontend
        |
        | HTTPS + JSON
        v
Amazon API Gateway (HTTP API)
        |
        v
AWS Lambda (Python)
   |       |        |
   |       |        +--> Amazon CloudWatch (logs and errors)
   |       |
   |       +--> Amazon DynamoDB (incident reports, if selected)
   |
   +--> Open-Meteo API (weather-model data)
   +--> S3 (reference data or snapshots, if needed)
   
Optional later: EventBridge for scheduled refreshes; SNS for useful alerts.
```

The diagram shows the intended design. AWS resources must be created and tested before being described as deployed.

## 3. Component responsibilities

### 3.1 Frontend — React and Vite

The frontend is responsible for:
- Showing historical ward exposure separately from current risk.
- Displaying risk level, score when calculable, reasons, and source/data status.
- Showing the timestamp and whether results are simulated.
- Providing the incident-report submission flow.
- Showing ward geography only after a suitable boundary dataset is verified.
- Presenting unavailable or stale data honestly.

The frontend consumes the shared API contract and can be developed initially with mock JSON. It must not calculate a separate risk score that disagrees with the backend.

### 3.2 Backend API — Python on AWS Lambda

The backend is responsible for:
- Exposing the agreed HTTP endpoints through API Gateway.
- Validating requests and normalizing response formats.
- Loading the historical reference dataset.
- Fetching or receiving normalized environmental inputs.
- Calling the independently testable risk engine.
- Reading and writing incident reports when persistence is implemented.
- Returning data freshness, provenance, and simulation metadata.
- Logging operational failures without exposing secrets or sensitive details.

The initial runtime decision is Python because the risk engine and data-processing work are naturally implemented and tested in Python. Local development should use the same application logic as Lambda wherever practical.

### 3.3 Weather adapter — Open-Meteo

Open-Meteo is the initial candidate for forecast/model data. The adapter should:
1. Request the selected Mumbai coordinates and required hourly precipitation fields.
2. Parse the provider response and preserve the requested coordinates and returned/grid-location metadata where available.
3. Keep forecast valid times distinct from retrieval time.
4. Validate units, missing values, and response shape.
5. Mark the result with its source, retrieval time, valid period, and data status.
6. Return an unavailable/stale state on failure rather than fabricating zero rainfall.

Forecast-model output is not the same as a direct rain-gauge observation. Do not label it “measured rainfall.” Begin with a single documented representative location for a reliable vertical slice; expand to multiple locations only when ward/location mapping is defensible. A single point must not be presented as a separate measurement for every ward.

### 3.4 Risk engine — independent Python module

The risk engine is a pure, independently testable module. It should accept structured inputs and return a structured assessment without making HTTP calls or writing to a database.

Inputs may include:
- Historical ward exposure and its provenance.
- Weather-model precipitation values, units, valid period, source, and freshness.
- Relevant citizen reports, including recency, verification status, and simulation flag.
- The assessment timestamp.

Outputs should include:
- `ward_code`
- `risk_score` (0–100 only when calculable; otherwise `null`)
- `risk_level` (`low`, `moderate`, `high`, or `unknown`)
- `reasons`
- Per-input `data_status`
- `calculated_at`
- `is_simulated`
- `method`

The score is an explainable heuristic, not a calibrated flood probability. The team must document and test weights, thresholds, and freshness rules before the score is used in the demo. Historical exposure alone cannot establish current flood risk. Missing or stale critical inputs must not silently become zero or low risk.

### 3.5 Historical reference data

The initial ward exposure CSV is a transcribed historical baseline associated with Census 2011 and a 250-metre exposure-buffer methodology. Preserve its original field names and provenance. Verify the transcription against the source report before presenting its exact figures as verified.

The dataset does not provide live flood locations, current ward population, or a validated probability of flooding.

### 3.6 Incident reports and persistence

The proposed API supports submitting reports and updating their workflow status. New reports start as unverified. Workflow status (`new`, `reviewed`, `resolved`) is separate from verification status (`unverified`, `verified`).

DynamoDB is the proposed store for report records if persistence is required by the MVP. Until it is implemented, local/in-memory or fixture-backed behaviour must be identified as prototype or simulated behaviour. Responder-only updates require authorization before any public deployment.

### 3.7 AWS storage and observability

- **API Gateway HTTP API:** public HTTPS entry point for the API.
- **AWS Lambda (Python):** request handling, data adapter, and risk-engine orchestration.
- **Amazon DynamoDB:** candidate persistence layer for incident reports.
- **Amazon S3:** optional storage for reference files or dated ingestion snapshots where versioning and object storage are useful.
- **Amazon CloudWatch:** Lambda logs, errors, and operational monitoring.
- **Amazon EventBridge:** optional scheduled weather refresh if caching/scheduled ingestion proves useful.
- **Amazon SNS:** optional notifications only if a real alert workflow is implemented.

Do not add a service merely to increase the AWS service count. Every deployed service should support a demonstrated requirement. Prefer IAM execution roles over embedded AWS credentials, and never commit credentials to Git.

## 4. Main data flow

1. The frontend requests ward baseline, risk assessments, and reports from the API.
2. The backend loads verified historical exposure values.
3. The weather adapter fetches and validates forecast/model data from Open-Meteo.
4. The backend gathers applicable incident reports and their status metadata.
5. The risk engine evaluates the available inputs and returns a score only when its rules permit one.
6. The API returns the result, explanation, source status, timestamps, and simulation labels.
7. The frontend displays historical exposure and current assessment as separate concepts.

For the initial local vertical slice, weather retrieval can be tested independently before it is connected to the risk engine. The application should remain useful for viewing historical baseline data when weather retrieval fails, but it must clearly state that current risk is unknown or unavailable.

## 5. API boundary

The shared interface is documented in [API_CONTRACT.md](API_CONTRACT.md). Planned endpoints:
- `GET /health`
- `GET /wards`
- `GET /risk`
- `GET /reports`
- `POST /reports`
- `PATCH /reports/{id}`

The API contract is the source of truth for response fields. Any changes must be agreed with the team and reflected in mock data and tests.

## 6. Configuration and security

- Use environment variables for non-secret configuration.
- Keep local populated `.env` files out of Git.
- Never expose server-only secrets through `VITE_*` variables; those values are bundled into frontend code.
- Use IAM roles for AWS service access.
- Validate report coordinates, category, description length, and all query parameters.
- Apply appropriate request limits and input validation.
- Restrict responder operations with authorization before treating the app as a real public service.
- Avoid collecting unnecessary personal data.

## 7. Failure and freshness behaviour

The system must distinguish `available`, `unavailable`, `stale`, and `simulated` inputs. Exact freshness thresholds must be based on provider update behaviour and documented before implementation.

If Open-Meteo cannot be reached, returns invalid data, or supplies data outside the accepted freshness policy:
- Do not substitute zero rainfall.
- Preserve the source failure/status.
- Do not claim a current risk level from historical exposure alone.
- Return an unknown/unavailable assessment where required.
- Keep historical baseline information available with its historical label.

A successful `GET /health` only confirms the API is responding; it does not guarantee that weather data or persistence is available.

## 8. Test strategy

Minimum checks:
- Python unit tests for risk-engine inputs and outputs.
- Weather-adapter tests for valid, missing, malformed, stale, and failed provider responses.
- API tests for the agreed JSON contract and validation errors.
- Report tests for invalid coordinates, unsupported categories, and unverified-by-default behaviour.
- Tests for missing/stale rainfall, no reports, unverified reports, and simulated inputs.
- Frontend checks for unknown-risk and data-status presentation.
- AWS smoke tests after deployment, including a health check and one real end-to-end request.

Use saved fixtures for deterministic tests; live provider calls should be a separate integration test, not the only test.

## 9. Team integration checkpoints

1. **Checkpoint 0 — contract agreement:** confirm endpoint schemas, risk-engine interface, data status meanings, runtime, and source choice.
2. **Checkpoint 1 — independent skeletons:** frontend mock screens, Python API skeleton, weather-adapter proof, and risk-engine module can run independently.
3. **Checkpoint 2 — demonstrable components:** each workstream records a short local demo and tests.
4. **Checkpoint 3 — local integration:** frontend calls the local API; API calls the risk engine; response schemas match.
5. **Checkpoint 4 — AWS integration:** deploy only the components needed for the end-to-end flow and verify permissions/logging.
6. **Checkpoint 5 — feature freeze and release:** stop adding features, fix blockers, verify all claims, and capture the actual working app for the demo video.

## 10. Current status and next actions

This document describes a proposed architecture; it does not certify that the API, weather adapter, risk engine, database, or AWS deployment is already operational.

Immediate implementation order:
1. Confirm the team accepts Python and Open-Meteo as the initial choices.
2. Create the Python backend skeleton and local health endpoint.
3. Make one real Open-Meteo request for a documented Mumbai point and record the response fields/units.
4. Add deterministic weather-adapter tests using fixtures.
5. Implement the risk-engine interface against the agreed contract.
6. Connect the local API and frontend before deploying to AWS.
