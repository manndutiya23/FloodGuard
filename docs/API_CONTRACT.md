# FloodGuard API Contract

**Status:** Draft for Checkpoint 0  
**Project:** FloodGuard — Mumbai hyperlocal flood intelligence

## 1. Purpose

This document defines how the FloodGuard frontend, backend, risk engine, and data layer exchange information.

All workstreams must follow these request and response formats. Changes must be communicated and reflected in the sample fixtures and tests.

## 2. Conventions

- API responses use JSON.
- Coordinates use decimal latitude and longitude.
- Timestamps use ISO 8601 format in UTC, ending in `Z`.
- Risk scores range from 0 to 100 when a score can be calculated.
- Risk levels are `low`, `moderate`, `high`, or `unknown`.
- Missing or stale environmental data must be identified explicitly.
- Historical vulnerability, observed incidents, forecast data, and simulated inputs must remain distinguishable.
- The API must never present simulated data as live observations.

## 3. Common error response

All API errors should use this structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid fields."
  },
  "request_id": "example-request-id"
}
```

The `request_id` may be omitted if unavailable. Error messages must not expose credentials, stack traces, or internal infrastructure details.

## 4. Endpoints

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

Returns ward-level historical vulnerability information and its provenance.

Example response:

```json
{
  "data": [
    {
      "ward_id": "WARD_01",
      "ward_name": "Example Ward",
      "historical_exposure": null,
      "source_year": 2011,
      "data_type": "historical_baseline"
    }
  ],
  "meta": {
    "source": "Mumbai Climate Action Plan vulnerability assessment",
    "updated_at": null
  }
}
```

**Important:** This is a structural example, not a real ward record. Replace example identifiers and values with verified dataset fields. Do not invent missing ward names, measurements, or update timestamps.

### GET /risk

Returns calculated risk results and the factors contributing to each result.

Example response:

```json
{
  "data": [
    {
      "ward_id": "WARD_01",
      "risk_score": 78,
      "risk_level": "high",
      "reasons": [
        "Elevated rainfall signal",
        "High historical vulnerability"
      ],
      "data_status": {
        "rainfall": "available",
        "historical_baseline": "available",
        "reports": "available"
      },
      "calculated_at": "2026-10-09T10:00:00Z",
      "is_simulated": true
    }
  ],
  "meta": {
    "risk_method": "heuristic",
    "data_mode": "simulation"
  }
}
```

The score and reasons above are illustrative only. They must not be treated as a real prediction or actual Mumbai measurement.

If a reliable score cannot be calculated, return `risk_score: null` and `risk_level: "unknown"` rather than manufacturing a result.

### GET /reports

Returns recent incident reports.

Optional query parameters may include:

- `status`: filter by report status.
- `ward_id`: filter by ward.
- `limit`: maximum number of results, within a configured server-side limit.

Example response:

```json
{
  "data": [
    {
      "report_id": "example-report-id",
      "ward_id": "WARD_01",
      "latitude": 19.0760,
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

The coordinates and description are illustrative. A real report must use its actual submitted location and content.

### POST /reports

Creates a new incident report.

Example request:

```json
{
  "latitude": 19.0760,
  "longitude": 72.8777,
  "category": "waterlogging",
  "description": "Water accumulating near Gate 2",
  "is_simulated": true
}
```

The backend must validate coordinates, category, description length, and required fields. The server assigns the report ID and timestamp.

Example successful response:

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

A successfully stored report is not automatically a verified flood observation.

### PATCH /reports/{id}

Updates an incident's status in the responder workflow.

Example request:

```json
{
  "status": "reviewed"
}
```

Allowed report statuses:

- `new`
- `reviewed`
- `resolved`

The backend validates the requested status and report ID.

Example successful response:

```json
{
  "data": {
    "report_id": "example-report-id",
    "status": "reviewed"
  }
}
```

Verification status is separate from workflow status. A report being reviewed does not automatically mean it has been verified.

## 5. Risk-engine interface

The risk engine must be testable independently of the API and frontend.

Its input should contain the available environmental signals, historical vulnerability, relevant incident information, timestamps, and source/freshness metadata.

Its output should contain:

- Ward or location identifier.
- Risk score, if calculable.
- Risk category.
- Reasons contributing to the result.
- Input availability and freshness information.
- Calculation timestamp.
- Whether the result uses simulated inputs.
- Method identifier, such as `heuristic`.

The precise input fields, normalization, weights, thresholds, and missing-data rules must be agreed and documented before implementation.

The risk engine must not assume that the historical ward vulnerability dataset is a flood-probability label.

## 6. HTTP status codes

Use appropriate HTTP responses:

- `200 OK`: successful retrieval or update.
- `201 Created`: report successfully created.
- `400 Bad Request`: malformed or invalid request.
- `404 Not Found`: report or resource does not exist.
- `429 Too Many Requests`: request limit exceeded, where configured.
- `500 Internal Server Error`: unexpected server failure.

## 7. Integration requirements

- The frontend must be able to use mock responses matching these schemas.
- The risk engine must accept local test fixtures.
- The backend must be testable using sample requests before the frontend is connected.
- Identifiers, timestamps, status values, and risk categories must remain consistent across workstreams.
- If a contract changes, update this document, the fixtures, and relevant tests.
- The final application must use the deployed API for the demonstrated end-to-end workflow.

## 8. Decisions still required

Before the contract is frozen, the team must confirm:

1. The actual ward identifiers and fields present in the reference CSV.
2. The final risk-engine input and output schema.
3. The supported incident categories.
4. The exact stale-data and missing-data status values.
5. The backend runtime and local testing approach.
6. The persistence implementation and API deployment configuration.

Until these decisions are approved at Checkpoint 0, this document is the proposed contract rather than a claim that the API has already been implemented.