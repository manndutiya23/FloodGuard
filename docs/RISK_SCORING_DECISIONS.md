# FloodGuard Risk-Scoring Decisions

**Status:** Agreed provisional prototype assumptions; subject to later validation  
**Date recorded:** 9 October 2026  
**Participants:** Manasvi and Mann  
**Implementation method:** `heuristic-v0.2`

This decision record captures the team's current risk-index behavior. These are implementation assumptions for a hackathon prototype, not scientifically validated flood-risk thresholds or probabilities. Keep the constants configurable in `backend/risk_engine.py` and revise this record when the team changes them.

## 1. Meaning of the score

- Output an explainable integer index from 0 to 100 only when a current rainfall input passes validation.
- The index is **not** a flood probability, a confirmed flood observation, or an official warning.
- The UI should show reasons, data freshness/status, source context, and the geographic limitation that the current weather input is one representative Mumbai point.
- Current display thresholds remain provisional: `low` for scores below 30; `moderate` for 30–59; `high` for 60–100. `unknown` is used when a meaningful new score cannot be computed.

## 2. Fixed score allocation

| Component | Maximum | Current calculation |
|---|---:|---|
| Rainfall | 70 | Linear scaling: `min(70, rainfall_mm / 30 * 70)`; 30 mm over the selected three-hour forecast window yields the maximum rainfall contribution. |
| Historical ward exposure | 20 | `clamp(exposure_percent, 0, 100) / 100 * 20`. The source statistic is historical vulnerability context, not flood probability. |
| Citizen reports | 10 | Sum the strongest decayed contribution from each scoring group, then cap at 10. |
| **Total** | **100** | Sum component contributions, round to an integer, and clamp to 0–100. |

The 30 mm benchmark is a heuristic scaling reference, not a validated rainfall danger threshold. The same rainfall normalization is currently applied to any accepted rainfall accumulation; observation input must preserve its actual period, and the scoring formula should be revisited if a suitable observation feed is integrated. Forecast accumulation itself must be exactly 180 minutes.

## 3. Forecast window and incomplete data

- The backend chooses exactly three consecutive hourly forecast periods that have not already started/passed. If evaluation occurs exactly at an hour boundary, that hour may be the first hour; otherwise start at the next whole hour.
- The forecast window is represented as `[forecast_window_start, forecast_window_end)`, exactly 180 minutes, with the end exclusive.
- Each raw hourly value has `forecast_valid_at`; the top-level provider response carries `retrieved_at`.
- Every required hourly value must exist and be a finite, non-negative millimetre amount. If a required value is missing or invalid, the new forecast accumulation is unavailable; do not skip it or replace it with zero.
- A window entirely in the past is stale. A window that overlaps elapsed time is invalid for a new score.
- If a new score cannot be computed, the API may return one separate `latest_available_info` object drawn from an actual usable provider value. That context must not be described as a newly calculated score. Its `retrieval_age_minutes` means elapsed time since `retrieved_at`, not time since `forecast_valid_at`.

## 4. Timestamp semantics and observation freshness

- `retrieved_at`: when FloodGuard fetched the provider payload.
- `observed_at`: when an observation was recorded; only valid for `kind: "observation"`.
- `forecast_valid_at`: time represented by one individual forecast hour.
- `forecast_window_start` and `forecast_window_end`: the derived three-hour forecast accumulation window.
- `evaluated_at` / `calculated_at`: when the assessment is evaluated/calculated.
- All timestamps use ISO 8601 UTC strings ending in `Z` in the application contract.
- Observation freshness limit: **180 minutes**, provisionally. An observation older than 180 minutes is stale; exactly 180 minutes old remains accepted. A malformed or future observation timestamp is rejected.
- Do not use `observed_at` as a forecast timestamp or confuse retrieval time with validity time.

## 5. Simulation

- Simulated inputs can be used for tests and demonstrations.
- A result influenced by simulated weather or report input must set `is_simulated: true` and be described as simulated, never as live weather or a real warning.
- Simulated data can be scored only if it otherwise meets validation rules.

## 6. Citizen reports: eligibility, weight, and decay

- Initial eligibility window: **120 minutes** before `evaluated_at`. Future-dated reports and reports at least 120 minutes old contribute zero.
- Each eligible report receives a provisional base contribution of **6 points if verified** and **2 points otherwise**. Verification must reflect an actual review; workflow state alone must not imply verification.
- Contribution decays linearly with age: `base_points * (1 - age_minutes / 120)`. The contribution is zero at 120 minutes. The aggregate report contribution is clamped to **10 points maximum**.
- The score calculation must remain at most 100; report volume never increases the overall maximum or changes the denominator.
- Reports with an explicit shared `duplicate_group_id` are scored as one group. Without that ID, reports become likely-duplicate candidates when they are both within **200 metres** and within **30 minutes** of each other and have compatible category/ward metadata. These thresholds are provisional and configurable.
- Within each likely-duplicate group, use only the strongest individual decayed contribution for scoring. Use deterministic complete-link grouping: a report joins a group only if it meets the candidate thresholds against every existing member, reducing chain merges. Original reports remain intact and available to the application/review process. A proximity/time match is a candidate grouping for scoring/review, **not proof the records describe the same incident**.
- Without coordinates or an explicit `duplicate_group_id`, reports remain separate groups. Independent scoring groups may reinforce the signal.
- The current engine has no ward-boundary geometry. For a ward-specific assessment, a report must already have an explicit matching `ward_code`; unmatched or unassigned reports do not contribute. If ward geometry is not implemented, explicit ward selection is an interim approach; PIN codes are not the primary ward-matching method.
- Additional implementation assumption: reports whose workflow status is `resolved` are excluded from the current incident contribution. Workflow state does not imply verification; `reviewed` reports still require their actual `verification_status` to determine weight.
- Report storage/input is not integrated into the live `/risk` endpoint yet. Engine tests with report fixtures do not mean that real reports affect live API results.

## 7. Missing inputs and response behavior

- Rainfall is required to calculate a new risk score. No rainfall, stale rainfall, malformed rainfall, or incomplete forecast window yields `risk_score: null`, `risk_level: "unknown"`, and an explanatory reason.
- Historical exposure alone must never produce a current score.
- Missing/stale values are not replaced by zero or interpreted as low risk.
- The API may provide `latest_available_info` separately from the current score, including source, value, `forecast_valid_at`, `retrieved_at`, and clearly defined retrieval age. It must not relabel this context as a newly calculated score.

## 8. Current limitations and follow-up

- Current live weather comes from a single representative Mumbai point, not ward-specific observations.
- Open-Meteo forecast output is model-based forecast data, not necessarily a rain-gauge observation.
- Citizen reports are supported by the pure risk-engine function for deterministic tests, but are not yet loaded/stored by the live `/risk` endpoint.
- Coordinate-based report grouping is an initial heuristic; grouping thresholds need review against actual data and must not delete the original reports.
- The heuristic has not been calibrated or evaluated against a validated set of historical flood outcomes.

## 9. Review/change process

Any change to the time windows, weights, thresholds, timestamp schema, duplicate-grouping logic, or missing-data behavior must update this file, `docs/API_CONTRACT.md`, implementation constants, fixtures, and tests in the same pull request. Keep values explicitly labelled provisional until there is a stronger evidence base.

**Agreed by:** Manasvi and Mann in discussion on 9 October 2026. Numeric values above reflect the agreed provisional assumptions; they are not claims of scientific validation.
