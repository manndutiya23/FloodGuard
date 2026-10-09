# FloodGuard API Contract

**Project:** FloodGuard — Mumbai Hyperlocal Flood Intelligence  
**Status:** Checkpoint 0 — Draft for implementation  
**Version:** 1.0

## 1. Purpose

This document defines how the FloodGuard frontend, backend, data layer, and risk engine communicate.

The goal is to allow all team members to work independently using agreed request formats, response schemas, and sample data.

Any changes to these shared interfaces must be communicated to the team and reflected in this document and the relevant tests.

## 2. General conventions

- API requests and responses use JSON unless otherwise specified.
- Timestamps use ISO 8601 format in UTC, ending in `Z`.
- Geographic coordinates use decimal degrees.
- Risk scores range from 0 to 100 when a score can be calculated.
- Risk levels are `low`, `moderate`, `high`, or `unknown`.
- Missing values must be represented as `null`, not as fabricated measurements.
- Historical vulnerability, current environmental signals, and citizen reports must remain distinguishable.
- Simulated inputs and outputs must be explicitly identified.
- The backend is responsible for validating requests and generating report IDs and timestamps.

## 3. Common error format

All API errors should follow this structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid fields."
  },
  "request_id": "example-request-id"
}
```

`request_id` may be omitted if unavailable.

Never expose credentials, secret configuration, or internal stack traces in API responses.

## 4. Historical ward exposure data

### GET /wards

Returns historical ward-level exposure information from the reference dataset.

The source CSV uses these actual fields:

| Field | Meaning |
|---|---|
| `ward_code` | Ward identifier from the source dataset |
| `population_potentially_exposed_within_250m_buffer` | Number of people potentially exposed within the assessed flood-risk buffer |
| `percentage_of_ward_population_potentially_exposed_percent` | Percentage of the ward population potentially exposed |
| `source` | Source report |
| `source_table` | Source table reference |
| `source_page` | Source page number |
| `underlying_population_data_year` | Year of the underlying population data |
| `data_type` | Classification of the dataset |

These source fields must be preserved during ingestion. The backend may add clearly documented API metadata, but must not silently rename or reinterpret the source measurements.

### Example response

```json
{
  "data": [
    {
      "ward_code": "A",
      "population_potentially_exposed_within_250m_buffer": null,
      "percentage_of_ward_population_potentially_exposed_percent": null,
      "source": "Mumbai Climate Action Plan vulnerability assessment",
      "source_table": "112",
      "source_page": 112,
      "underlying_population_data_year": 2011,
      "data_type": "historical_vulnerability_baseline"
    }
  ],
  "meta": {
    "data_type": "historical_vulnerability_baseline"
  }
}
```

**This is a schema example, not an actual ward record.** The `null` measurements must be replaced with verified values from the CSV when the API is implemented. The example's source metadata must also be checked against the actual CSV before use.

### Display requirements

The frontend should display both:

1. The number of people potentially exposed.
2. The percentage of the ward population potentially exposed.

These values describe historical assessed exposure, not the number of people currently experiencing flooding.

The interface must clearly label the figures as historical and show the underlying population-data year where available.

A ward with a higher historical exposure value must not automatically be described as experiencing a current flood.

## 5. Current flood-risk assessment

### GET /risk

Returns the risk assessment produced by the risk engine.

The assessment may use available rainfall information, historical vulnerability, and relevant citizen incident reports.

The exact calculation method, thresholds, input schema, and missing-data rules must be documented separately in the risk-engine implementation.

### Example response

```json
{
  "data": [
    {
      "ward_code": "A",
      "risk_score": null,
      "risk_level": "unknown",
      "reasons": [],
      "data_status": {
        "rainfall": "unavailable",
        "historical_baseline": "available",
        "reports": "unavailable"
      },
      "calculated_at": "2026-10-09T10:00:00Z",
      "is_simulated": true,
      "method": "heuristic"
    }
  ],
  "meta": {
    "data_mode": "simulation"
  }
}
```

This example demonstrates an unknown risk result when current signals are unavailable. Its timestamp and status values are illustrative.

### Requirements

- Historical exposure and current risk must be displayed as separate measures.
- Every risk result must provide an explanation where one can be calculated.
- A score must not be invented when the required inputs are unavailable.
- `unknown` is a valid result and must not be converted into `low`.
- The frontend must identify simulated assessments.
- Risk scores must not be presented as calibrated flood probabilities unless a suitable model has been trained and evaluated to support that interpretation.

## 6. Citizen incident reports

### GET /reports

Returns incident reports, with optional filters:

- `ward_code`: filter by ward.
- `status`: filter by workflow status.
- `limit`: maximum number of results, subject to a server-side limit.

Example response:

```json
{
  "data": [
    {
      "report_id": "example-report-id",
      "ward_code": "A",
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

The example location and report are illustrative, not a real incident.

### POST /reports

Creates a citizen incident report.

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

The backend must validate coordinates, required fields, description length, and supported categories.

The backend generates the report ID and timestamp. It must not automatically mark a new report as verified.

Example success response:

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

Use HTTP `201 Created` for a successfully created report.

## 7. Responder workflow

### PATCH /reports/{id}

Updates the workflow status of an existing report.

Example request:

```json
{
  "status": "reviewed"
}
```

Supported workflow statuses:

- `new`
- `reviewed`
- `resolved`

The backend must validate the report ID and requested status.

Workflow status and verification status are separate fields. Reviewing a report does not automatically prove that the reported incident occurred.

The final implementation must define appropriate authorization for responder-only updates.

## 8. Risk-engine interface

The risk engine must be independently testable without the API or frontend.

Its input must contain the environmental signals and historical vulnerability information available for the assessment, together with relevant source, timestamp, and freshness metadata.

Its output must contain:

- `ward_code` or another documented location identifier.
- `risk_score`, if calculable.
- `risk_level`.
- `reasons`.
- `data_status`.
- `calculated_at`.
- `is_simulated`.
- `method`.

The exact input schema, score normalization, weights, thresholds, and missing-data rules remain decisions for Checkpoint 0.

The risk engine must not interpret the historical exposure count or percentage as a labelled flood probability.

## 9. Health check

### GET /health

Checks whether the API is responding.

Example response:

```json
{
  "status": "ok",
  "service": "floodguard-api"
}
```

A successful health check indicates that the API is responding. It does not necessarily mean every external data source is available.

## 10. HTTP status codes

Use appropriate HTTP status codes:

- `200 OK`: successful retrieval or update.
- `201 Created`: report successfully created.
- `400 Bad Request`: invalid request.
- `404 Not Found`: resource does not exist.
- `429 Too Many Requests`: request limit exceeded, where configured.
- `500 Internal Server Error`: unexpected server failure.

Error responses must use the common error structure defined in Section 3.

## 11. Independent development and testing

Each workstream must be testable without requiring the others to finish first.

- **Frontend:** use mock JSON responses that follow this contract.
- **Risk engine:** use local test fixtures with known inputs and expected outputs.
- **Backend:** test endpoints independently using sample requests.
- **Documentation and demo:** use the contract to describe planned behaviour, but label features as implemented only after verification.

Integration begins once each component has a demonstrable independent version.

## 12. Decisions required before contract freeze

The team must confirm:

1. The exact CSV field values and provenance.
2. The final risk-engine input and output schema.
3. Supported incident categories.
4. Missing-data and stale-data conventions.
5. Backend runtime and local testing approach.
6. Persistence and deployment configuration.
7. Authorization requirements for responder operations.
8. The final definition of simulated versus real data.

Until these decisions are approved, this document remains the proposed integration contract. Implementation details may be refined at Checkpoint 0, but all changes must be shared with the team.