# FloodGuard API Contract

**Status:** Shared implementation target; prototype risk parameters are explicitly provisional  
**Project:** FloodGuard — Mumbai hyperlocal flood intelligence  
**Related decision record:** `docs/RISK_SCORING_DECISIONS.md`

This document defines the shared API and risk-engine interfaces. Frontend, backend, and data workstreams should use these field names and status values. Any contract change must be communicated and reflected in fixtures and tests.

## 1. Conventions

- API payloads use JSON.
- Coordinates are decimal latitude and longitude.
- API timestamps are ISO 8601 UTC strings ending in `Z`.
- Ward identifiers use the reference dataset's `ward_code` values (for example, `F/N`), not invented IDs.
- A risk score is an explainable prototype index from 0 to 100, not a flood probability, confirmed flood observation, or official warning.
- Risk levels are `low`, `moderate`, `high`, or `unknown`.
- Data status values are `available`, `unavailable`, `stale`, or `simulated`.
- Report workflow statuses are `new`, `reviewed`, and `resolved`.
- Report verification statuses are `unverified` and `verified`. Verification must reflect an actual review process; it must not be inferred from workflow status.
- Historical exposure, observations, forecasts, citizen reports, and simulated data must remain distinguishable.
- Missing data must not silently be treated as zero.

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

```json
{
  "status": "ok",
  "service": "floodguard-api"
}
```

### GET /wards

Returns the historical ward-exposure baseline and provenance from the reference CSV.

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

The response must preserve the source's ward codes and available field names. Do not invent ward names or update timestamps that are not present in the source. Historical ward exposure is background vulnerability context, not a live flood boundary or flood-probability value.

### GET /weather

Returns provider weather-model data for the configured representative Mumbai point. The response must identify the source, status, requested location, provider-returned location where supplied, units, retrieval time, and forecast-valid timestamps.

A normalized forecast-hour record uses this shape:

```json
{
  "forecast_valid_at": "2026-10-09T11:00:00Z",
  "precipitation_mm": 2.5
}
```

`forecast_valid_at` is the forecast period's valid timestamp. It is not the time FloodGuard retrieved the response. The top-level weather result uses `retrieved_at` for retrieval time. Do not use `observed_at` for forecast records.

Provider coordinates may represent a model grid location and may differ from requested coordinates. One representative point is not independent weather data for every ward.

### GET /risk

Returns one assessment per evaluated ward or location. `ward_code` may be supplied as an optional query parameter if supported by the deployed implementation. A current score must only be returned when the selected inputs are sufficiently complete and valid.

Example successful assessment (illustrative only):

```json
{
  "data": [
    {
      "ward_code": "F/N",
      "risk_score": 58,
      "risk_level": "moderate",
      "reasons": [
        "Forecast precipitation contributes to the prototype index.",
        "Historical ward exposure contributes background context."
      ],
      "data_status": {
        "rainfall": "available",
        "historical_baseline": "available",
        "reports": "unavailable"
      },
      "calculated_at": "2026-10-09T10:00:00Z",
      "is_simulated": false,
      "method": "heuristic-v0.2",
      "latest_available_info": null
    }
  ],
  "meta": {
    "risk_method": "heuristic-v0.2",
    "data_mode": "live_weather_with_historical_baseline",
    "location_scope": "Representative Mumbai point only; not ward-specific weather"
  }
}
```

The values above are illustrative, not real measurements. A score is an explainable prototype index, not a calibrated probability, flood confirmation, or official warning. UI text must explain contributing reasons and data limitations.

When a meaningful new score cannot be calculated, return `risk_score: null`, `risk_level: "unknown"`, and reasons explaining why. Historical exposure alone must never generate a current risk score.

#### Latest usable information when a new score is unavailable

`latest_available_info` is API-level explanatory context, not a risk score and not a replacement for one. It may be an object or `null`. It must be based only on real source values available to the request and must never claim that a new score was calculated. Include provenance and the relevant times. For forecast data, include `forecast_valid_at`; include `retrieved_at` separately. If age is reported, define whether it is age since retrieval or time distance from the forecast-valid time and label it accordingly.

Example only:

```json
{
  "risk_score": null,
  "risk_level": "unknown",
  "reasons": [
    "A complete three-hour forecast window was not available, so a new risk score was not calculated."
  ],
  "data_status": {
    "rainfall": "unavailable",
    "historical_baseline": "available",
    "reports": "unavailable"
  },
  "calculated_at": "2026-10-09T10:00:00Z",
  "is_simulated": false,
  "method": "heuristic-v0.2",
  "latest_available_info": {
    "kind": "forecast",
    "precipitation_mm": 8.2,
    "unit": "mm",
    "forecast_valid_at": "2026-10-09T09:00:00Z",
    "retrieved_at": "2026-10-09T09:05:00Z",
    "source": "Open-Meteo",
    "is_simulated": false
  }
}
```

The example's values and wording are illustrative only. Any user-facing statement such as “heavy rainfall was forecast” must be supported by the actual value, time window, and an explicit interpretation rule. Do not turn a partial forecast window into a new score. Latest usable information may still be exposed with its actual timestamp even if the score is unavailable.

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

Creates an incident report. The client supplies location and report details; the server assigns the ID, timestamp, workflow status, and initial verification status.

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

For a real user submission, the client must not be allowed to mark a report as verified. Synthetic reports must be visibly labelled, and their simulated status must be controlled by the application/backend rather than trusted blindly from arbitrary client input.

Example response (`201 Created`):

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

Workflow status and verification status are separate. Moving a report to `reviewed` does not automatically make it verified. Until authentication/authorization is implemented, this endpoint is a prototype workflow and must not be represented as secure public responder access.

## 4. Risk-engine interface

The risk engine is a pure, independently testable calculation module. It must not make HTTP requests or write to a database. The backend gathers and validates inputs, invokes the engine, and handles API serialization and persistence.

### Input object

Optional inputs may be unavailable, but absence must never be silently replaced with zero.

Observation example:

```json
{
  "ward": {
    "ward_code": "F/N",
    "population_potentially_exposed_within_250m_buffer": 355766,
    "percentage_of_ward_population_potentially_exposed_percent": 66.8,
    "underlying_population_data_year": 2011
  },
  "rainfall": {
    "kind": "observation",
    "value": 4.5,
    "unit": "mm",
    "period_minutes": 60,
    "observed_at": "2026-10-09T09:30:00Z",
    "retrieved_at": "2026-10-09T09:31:00Z",
    "source": "configured-provider",
    "status": "available",
    "is_simulated": false
  },
  "reports": [],
  "evaluated_at": "2026-10-09T10:00:00Z"
}
```

Derived three-hour forecast input example:

```json
{
  "rainfall": {
    "kind": "forecast",
    "value": 12.0,
    "unit": "mm",
    "period_minutes": 180,
    "forecast_window_start": "2026-10-09T10:00:00Z",
    "forecast_window_end": "2026-10-09T13:00:00Z",
    "retrieved_at": "2026-10-09T09:55:00Z",
    "source": "Open-Meteo",
    "status": "available",
    "is_simulated": false
  }
}
```

Timestamps have distinct meanings:

- `retrieved_at`: when FloodGuard retrieved the provider data.
- `observed_at`: when an observation was recorded; valid only for `kind: "observation"`.
- `forecast_valid_at`: valid time of an individual hourly forecast item from the weather adapter.
- `forecast_window_start` and `forecast_window_end`: the half-open interval represented by the derived three-hour accumulation; `period_minutes` must be 180 for that forecast signal.
- `evaluated_at`: when the engine assessed the input.

Never substitute one timestamp type for another. In particular, do not use `observed_at` for a forecast. Retain the provider response's retrieval timestamp separately from forecast-valid timestamps.

### Forecast-window rules

- Build the initial forecast input from exactly three consecutive, future hourly precipitation values, with a three-hour window.
- Do not use forecast hours whose valid periods have already passed at evaluation time.
- If any of the three required hourly precipitation values is missing or invalid, do not silently omit it or replace it with zero. Mark the new forecast input unavailable and do not calculate a new risk score from an incomplete window.
- If an entire forecast window has passed, mark it stale/unusable. If the proposed window overlaps elapsed time or cannot be assembled as three future consecutive hours, it is not a valid new scoring window.
- The API may separately return latest usable weather information with its actual timestamp and retrieval time. This context must not be labelled as a freshly calculated risk score.

### Observation freshness

The observation freshness limit is provisionally 180 minutes. An observation older than the limit is stale. An observation timestamp in the future or an invalid timestamp is rejected. The limit is a prototype assumption and must be reviewed against any future observation provider's reporting interval.

### Output object

The engine returns a score only when the required weather input passes validation and is complete.

```json
{
  "ward_code": "F/N",
  "risk_score": 58,
  "risk_level": "moderate",
  "reasons": [
    "Forecast precipitation contributes to the prototype index.",
    "Historical ward exposure contributes background context."
  ],
  "data_status": {
    "rainfall": "available",
    "historical_baseline": "available",
    "reports": "unavailable"
  },
  "calculated_at": "2026-10-09T10:00:00Z",
  "is_simulated": false,
  "method": "heuristic-v0.2",
  "score_components": {
    "rainfall_points": 28.0,
    "historical_exposure_points": 13.36,
    "citizen_report_points": 0.0,
    "maximum_total_points": 100
  }
}
```

When a meaningful new score cannot be calculated, `risk_score` must be `null`, `risk_level` must be `unknown`, and `reasons` must explain why. The API layer may attach a separate `latest_available_info` object as described above.

### Scoring contributions and risk-level thresholds

The agreed maximum contributions are fixed:

| Signal | Maximum contribution |
|---|---:|
| Rainfall | 70 points |
| Historical exposure | 20 points |
| Citizen reports | 10 points |
| **Total maximum** | **100 points** |

The combined score must never exceed 100. The total maximum must not change dynamically based on report volume. Report influence must be normalized within its fixed ten-point allocation.

The existing risk-level thresholds remain provisional: `low` for scores below 30, `moderate` for scores from 30 through 59, and `high` for scores from 60 through 100. These levels and the weights are prototype assumptions, not scientifically validated flood-risk probabilities.

The provisional numeric assumptions are recorded in `docs/RISK_SCORING_DECISIONS.md`: rainfall is linearly normalized so 30 mm over the selected three-hour forecast window yields 70 rainfall points; verified/unverified report base contributions are 6/2 points with linear decay to zero over 120 minutes; likely-duplicate candidate thresholds are 200 metres and 30 minutes. These values remain configurable prototype assumptions, not validated hazard thresholds.

### Citizen-report rules

- The provisional eligibility window is two hours from `reported_at` to `evaluated_at`.
- Report contribution must decay gradually with age rather than dropping sharply at an arbitrary intermediate boundary.
- Verified reports may contribute more than unverified reports, but verification must reflect an actual review process.
- Similar, independent reports from the same nearby area and a similar time window may reinforce an incident signal.
- Reports with a shared `duplicate_group_id` are scored as one group. Without that ID, reports with coordinates within 200 metres and report times within 30 minutes are provisional duplicate candidates when their category/ward metadata are compatible; the thresholds are configurable prototype assumptions.
- Each group contributes only its strongest individual decayed contribution. Use deterministic complete-link grouping: a candidate must meet the configured distance/time thresholds against every member already in a group, reducing chain merges. This grouping is for scoring/review only, not confirmation that reports are duplicates. Preserve original records; independent groups can reinforce the signal.
- Verified reports use a provisional base contribution of 6 points; unverified reports use 2 points. For either type, use linear decay: `base_points * (1 - age_minutes / 120)`. Reports at least 120 minutes old or in the future contribute zero.
- Additional implementation assumption: `resolved` reports do not contribute to a current incident score. A ward-specific score requires an explicit upstream ward match while ward-boundary geometry is unavailable; an unassigned report must not be added to every ward by default.
- Aggregate report contribution cannot exceed ten points, and the total score cannot exceed 100.
- Prefer coordinates and ward-boundary geometry for ward matching. If suitable geometry is not yet available, use explicit ward selection as an interim approach. Do not use PIN codes as the primary ward-matching method.
- The live `/risk` endpoint must not claim to use citizen reports until report storage/input integration is implemented. Tests using in-memory report fixtures do not imply the API integration exists.

### Simulation and missing data

- A simulated input may produce a score for demonstration purposes, but all resulting assessment data must be labelled simulated.
- If real and simulated inputs are mixed, the result must still be labelled as simulated/mixed rather than wholly live.
- Missing or stale rainfall must not silently become zero or low risk.
- Historical exposure alone must never produce a current-risk score.
- Reasons must distinguish forecast-based signals from observed rainfall and must not claim flooding has been confirmed.

## 5. HTTP status codes

- `200 OK`: successful retrieval or update.
- `201 Created`: report created.
- `400 Bad Request`: malformed or invalid request.
- `404 Not Found`: report/resource does not exist.
- `429 Too Many Requests`: request limit exceeded, where configured.
- `500 Internal Server Error`: unexpected server failure.

## 6. Integration and testing requirements

- Frontend development can use mock JSON matching these response schemas before the backend is deployed.
- The risk engine must be callable and testable independently with deterministic fixtures.
- Keep ward identifiers, timestamp names, units, enum values, and status behavior consistent across the weather adapter, risk engine, API contract, fixtures, and frontend.
- Cover complete and incomplete forecast windows, elapsed forecast periods, stale/future/malformed observation timestamps, simulated inputs, report expiry and decay, duplicate grouping, missing weather, invalid values, and score bounds.
- If the contract changes, update the document, implementation, fixtures, and tests in the same change.
- A test of an in-memory capability does not establish that a live API endpoint integrates or persists that input.
- The final demo must use the integrated application for the workflow it claims to demonstrate.

## 7. Contract status and limitations

This document describes the implementation target, not proof that every behavior is already implemented. The numeric normalization constant for rainfall and the report decay/base weights/duplicate thresholds require explicit recording in `docs/RISK_SCORING_DECISIONS.md` before the complete configuration is considered final.

The current weather source uses one representative Mumbai point, not ward-specific rainfall. The rainfall scaling rule is linear and capped at 70 points, where 30 mm over the selected three-hour forecast window reaches the cap; this is not a validated rainfall danger threshold. The heuristic has not been scientifically validated and must not be described as a flood-prediction model or official warning. Current data or storage limitations must be surfaced rather than hidden.
