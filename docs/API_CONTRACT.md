# FloodGuard API Contract

**Status:** Checkpoint 0 contract — agreed implementation target  
**Project:** FloodGuard — Mumbai hyperlocal flood intelligence

This document defines the shared API and risk-engine interfaces. Frontend, backend, and data workstreams should use these field names and status values. Any change must be communicated and reflected in fixtures and tests.

## 1. Conventions

- API payloads use JSON.
- Coordinates are decimal latitude and longitude.
- Timestamps are ISO 8601 UTC strings ending in `Z`.
- Ward identifiers use the source dataset's `ward_code` values (for example, `F/N`), not invented IDs.
- Risk scores range from 0 to 100 when a meaningful score can be calculated.
- Risk levels are `low`, `moderate`, `high`, or `unknown`.
- Data status values are `available`, `unavailable`, `stale`, or `simulated`.
- Report workflow statuses are `new`, `reviewed`, and `resolved`.
- Report verification statuses are `unverified` and `verified`. Verification must reflect an actual review process; it must not be inferred from workflow status.
- Historical, observed, forecast, and simulated data must remain distinguishable.

## 2. Common error response

All API errors should follow this shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid fields."
  },
  "request_id": "example-request-id"
}
```

`request_id` may be omitted if unavailable. Never expose credentials, stack traces, or internal infrastructure details.

## 3. Endpoints

### GET /health

Checks whether the API is responding.

Example response:

```json
{
  "status": "ok",
  "service": "floodguard-api"
}
```

### GET /wards

Returns the historical ward-exposure baseline and provenance from the reference CSV.

Example response (illustrative values; field names match the CSV):

```json
{
  "data": [
    {
      "ward_code": "F/N",
      "population_potentially_exposed_within_250m_buffer": 355766,
      "percentage_of_ward_population_potentially_exposed_percent": 66.8,
      "underlying_population_data_year": 2011,
      "data_type": "historical vulnerability baseline; not a live flood prediction"
    }
  ],
  "meta": {
    "source": "Mumbai Climate Action Plan - Climate & Air Pollution Risks and Vulnerability Assessment",
    "source_page": 112
  }
}
```

The response must preserve the source's ward codes and available field names. Do not invent ward names or update timestamps that are not present in the source. Verify transcribed figures against the original report before presenting them as confirmed.

### GET /risk

Returns one risk assessment per evaluated ward or location. Optional filters may be added later only if needed.

Example response:

```json
{
  "data": [
    {
      "ward_code": "F/N",
      "risk_score": 72,
      "risk_level": "high",
      "reasons": [
        "Elevated rainfall signal",
        "High historical exposure baseline",
        "Recent incident reports are present"
      ],
      "data_status": {
        "rainfall": "available",
        "historical_baseline": "available",
        "reports": "available"
      },
      "calculated_at": "2026-10-09T10:00:00Z",
      "is_simulated": true,
      "method": "heuristic"
    }
  ],
  "meta": {
    "risk_method": "heuristic",
    "data_mode": "simulation"
  }
}
```

The score and reasons above are examples only, not real measurements or a validated prediction. If a meaningful current assessment cannot be calculated, return `risk_score: null` and `risk_level: "unknown"`. Historical exposure alone must not generate a current flood-risk score.

### GET /reports

Returns recent incident reports. Supported optional query parameters:

- `status`: workflow status filter.
- `ward_code`: ward filter, when the report can be reliably associated with a ward.
- `limit`: result limit, capped by a server-side maximum.

Example response:

```json
{
  "data": [
    {
      "report_id": "example-report-id",
      "ward_code": "F/N",
      "latitude": 19.076,
      "longitude": 72.8777,
      "category": "waterlogging",
      "description": "Water accumulating near Gate 2",
      "status": "new",
      "verification_status": "unverified",
      "reported_at": "2026-10-09T10:00:00Z",
      "is_simulated": true
    }
  ]
}
```

Coordinates and report text are illustrative. A report without a reliably matched ward may use `ward_code: null`; do not guess the ward.

### POST /reports

Creates an incident report. The client supplies the location and report details; the server assigns the ID, timestamp, workflow status, and initial verification status.

Example request:

```json
{
  "latitude": 19.076,
  "longitude": 72.8777,
  "category": "waterlogging",
  "description": "Water accumulating near Gate 2",
  "is_simulated": true
}
```

For a real user submission, the client must not be allowed to mark a report as verified. In the public demo, synthetic reports must be visibly labelled and their simulated status must be controlled safely by the application/backend, not trusted blindly from arbitrary client input.

Example successful response (`201 Created`):

```json
{
  "data": {
    "report_id": "generated-report-id",
    "status": "new",
    "verification_status": "unverified",
    "reported_at": "2026-10-09T10:00:00Z",
    "is_simulated": true
  }
}
```

Validate coordinates, category, and description length. A successfully stored report is not automatically a verified flood observation.

### PATCH /reports/{id}

Updates a report's workflow status.

Example request:

```json
{
  "status": "reviewed"
}
```

Allowed values: `new`, `reviewed`, `resolved`.

Example response:

```json
{
  "data": {
    "report_id": "example-report-id",
    "status": "reviewed"
  }
}
```

Workflow status and verification status are separate. Moving a report to `reviewed` does not automatically make it verified. Until authentication/authorization is implemented, this endpoint is a prototype workflow and must not be represented as secure public responder access.

## 4. Risk-engine interface

The risk engine is a pure, independently testable calculation module. It should not make HTTP requests or write to the database itself. The backend gathers inputs, calls the engine, and handles persistence/API responses.

### Input object

The backend supplies an object with the following conceptual shape. Optional inputs may be `null` when unavailable; absence must never be silently replaced with zero.

```json
{
  "ward": {
    "ward_code": "F/N",
    "population_potentially_exposed_within_250m_buffer": 355766,
    "percentage_of_ward_population_potentially_exposed_percent": 66.8,
    "underlying_population_data_year": 2011,
    "data_type": "historical vulnerability baseline"
  },
  "rainfall": {
    "kind": "observation",
    "value": 42.5,
    "unit": "mm",
    "period_minutes": 60,
    "observed_at": "2026-10-09T09:30:00Z",
    "source": "configured-provider",
    "status": "available"
  },
  "reports": [
    {
      "report_id": "example-report-id",
      "reported_at": "2026-10-09T09:45:00Z",
      "status": "new",
      "verification_status": "unverified",
      "is_simulated": false
    }
  ],
  "evaluated_at": "2026-10-09T10:00:00Z"
}
```

The values are illustrative. The actual rainfall provider, units, time window, and freshness thresholds must be documented once the provider is selected. Rainfall `kind` must distinguish `observation` from `forecast`; the provider's source and timestamp must be retained. A missing rainfall object or non-available status must be represented explicitly.

### Output object

```json
{
  "ward_code": "F/N",
  "risk_score": 72,
  "risk_level": "high",
  "reasons": [
    "Elevated rainfall signal",
    "High historical exposure baseline"
  ],
  "data_status": {
    "rainfall": "available",
    "historical_baseline": "available",
    "reports": "available"
  },
  "calculated_at": "2026-10-09T10:00:00Z",
  "is_simulated": false,
  "method": "heuristic"
}
```

If the available inputs cannot support a meaningful current assessment, `risk_score` must be `null`, `risk_level` must be `unknown`, and `reasons` must explain why. The output must indicate whether any contributing input is simulated. If simulated and real inputs are mixed, the result must still be labelled as simulation/mixed rather than wholly live.

### Risk-engine rules

1. Historical exposure is a background vulnerability factor, not a flood-probability label.
2. A current risk assessment must not be generated from historical exposure alone.
3. Rainfall observations and forecasts must not be treated as interchangeable.
4. Reports contribute according to recency and verification status; unverified reports must not be described as confirmed incidents.
5. Do not double-count overlapping signals.
6. Missing or stale inputs must be surfaced in `data_status`; they must not silently become zero or low risk.
7. Every score must have human-readable reasons and a method identifier.
8. The initial method is a heuristic, not a trained or validated flood-prediction model.

### Scoring configuration still to be set during implementation

The interface is fixed, but numeric weights and thresholds are deliberately not fixed here. They depend on the actual rainfall source, its units/time window, and available incident data. Before enabling the score, the team must document:
- signal normalization and weights;
- risk-level thresholds;
- source-specific freshness thresholds;
- treatment of unverified reports and simulated inputs;
- missing-input behaviour;
- tests for edge cases.

Do not choose weights merely to make the demo produce dramatic high-risk results.

## 5. HTTP status codes

- `200 OK`: successful retrieval or update.
- `201 Created`: report created.
- `400 Bad Request`: malformed or invalid request.
- `404 Not Found`: report/resource does not exist.
- `429 Too Many Requests`: request limit exceeded, where configured.
- `500 Internal Server Error`: unexpected server failure.

## 6. Integration requirements

- Frontend development can use mock JSON matching these response schemas before the backend is deployed.
- The risk engine must be callable and testable independently using local fixtures.
- Keep ward identifiers, timestamps, enum values, and field names consistent across workstreams.
- Add tests for missing/stale rainfall, no reports, unverified reports, simulated inputs, invalid coordinates, and unknown ward codes.
- If the contract changes, update this document, fixtures, and tests in the same change.
- The final demo must use the integrated application for the workflow it claims to demonstrate.

## 7. Contract status

The API routes, shared field names, and risk-engine input/output shape are the implementation target for Checkpoint 0. The actual rainfall provider, scoring weights, thresholds, persistence choice, and deployment configuration remain implementation decisions and must be recorded once confirmed. This document describes the agreed interface, not features already implemented.
