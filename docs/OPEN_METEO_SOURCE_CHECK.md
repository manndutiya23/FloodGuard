# Open-Meteo Real Request Source Check

**Outcome: PASS — endpoint response and expected fields validated**

- **Date checked:** 2026-10-09 (UTC)
- **Retrieval started:** `2026-10-09T16:17:32Z`
- **Retrieval completed:** `2026-10-09T16:17:36Z`
- **HTTP status:** 200
- **Request outcome:** HTTP request succeeded and required coordinates, timezone, hourly time series, and precipitation units validated.
- **Validation:** No required-field validation errors.
- **Endpoint:** `https://api.open-meteo.com/v1/forecast`
- **Exact request URL:** `https://api.open-meteo.com/v1/forecast?latitude=19.076&longitude=72.8777&hourly=precipitation&forecast_days=2&timezone=UTC`
- **Requested parameters:** `hourly=precipitation`, `forecast_days=2`, `timezone=UTC`
- **Requested coordinates:** latitude `19.076`, longitude `72.8777`
- **Provider-returned coordinates:** latitude `19.086115`, longitude `72.85291`
- **Returned elevation:** `6.0` metres (where supplied)
- **Precipitation units:** requested/expected `mm`; provider returned `mm`
- **Timezone:** requested `UTC`; provider returned `GMT` (abbreviation `GMT`, UTC offset seconds `0`)
- **Forecast valid-time coverage:** `2026-10-09T00:00` through `2026-10-10T23:00`
- **Valid-time count / cadence:** 48 timestamps; requested hourly data over two forecast days.
- **All returned valid times (UTC):** `2026-10-09T00:00`, `2026-10-09T01:00`, `2026-10-09T02:00`, `2026-10-09T03:00`, `2026-10-09T04:00`, `2026-10-09T05:00`, `2026-10-09T06:00`, `2026-10-09T07:00`, `2026-10-09T08:00`, `2026-10-09T09:00`, `2026-10-09T10:00`, `2026-10-09T11:00`, `2026-10-09T12:00`, `2026-10-09T13:00`, `2026-10-09T14:00`, `2026-10-09T15:00`, `2026-10-09T16:00`, `2026-10-09T17:00`, `2026-10-09T18:00`, `2026-10-09T19:00`, `2026-10-09T20:00`, `2026-10-09T21:00`, `2026-10-09T22:00`, `2026-10-09T23:00`, `2026-10-10T00:00`, `2026-10-10T01:00`, `2026-10-10T02:00`, `2026-10-10T03:00`, `2026-10-10T04:00`, `2026-10-10T05:00`, `2026-10-10T06:00`, `2026-10-10T07:00`, `2026-10-10T08:00`, `2026-10-10T09:00`, `2026-10-10T10:00`, `2026-10-10T11:00`, `2026-10-10T12:00`, `2026-10-10T13:00`, `2026-10-10T14:00`, `2026-10-10T15:00`, `2026-10-10T16:00`, `2026-10-10T17:00`, `2026-10-10T18:00`, `2026-10-10T19:00`, `2026-10-10T20:00`, `2026-10-10T21:00`, `2026-10-10T22:00`, `2026-10-10T23:00`
- **Weather data type:** forecast/model output, not direct rain-gauge observations.
- **Representative location note:** the single point `19.076, 72.8777` is used only for this smoke test; it does not establish ward-level or street-level coverage.

## Usage terms and attribution

Official documentation: https://open-meteo.com/en/docs

Terms and pricing pages reviewed on **2026-10-09**: https://open-meteo.com/en/terms and https://open-meteo.com/en/pricing. The free API is for non-commercial use, subject to provider limits, and does not provide an uptime guarantee. Weather data is licensed under CC BY 4.0; provide appropriate credit and a link to the licence. Suggested visible attribution: **Weather data by Open-Meteo.com** (https://open-meteo.com/). Re-check the current terms before public deployment or any commercial use.

Licence: https://creativecommons.org/licenses/by/4.0/

## Limitations

A successful HTTP/schema check verifies only that this request returned the expected response structure and metadata at the recorded time. It does **not** validate forecast accuracy, model skill, future uptime, local rain-gauge agreement, flood prediction, or the suitability of one coordinate for every Mumbai ward. Open-Meteo may return a nearby model-grid coordinate rather than exactly the requested point. Precipitation is not proof of flooding or waterlogging.

## Error details

None reported.
