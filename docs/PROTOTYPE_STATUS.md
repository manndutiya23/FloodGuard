# Prototype status and verified behavior

**Last updated:** 2026-10-11  
**Status:** Working prototype; not production-ready.

This document separates behavior exercised against the current deployment from planned work. It is a checkpoint, not a claim that every feature or failure path has been tested.

## Verified against the deployed AWS-backed application

- `GET /health` returned `{"status":"ok","service":"floodguard-api"}`.
- Citizen report submission is connected to the deployed API and DynamoDB persistence.
- Optional photo evidence accepts JPEG, PNG, and WebP images up to 5 MiB.
- `POST /reports/photo-upload` returns a short-lived presigned S3 POST form.
- A browser upload to the private S3 bucket succeeded with `204 No Content`.
- `POST /reports` validated the uploaded object and created the associated report with `201 Created`.
- S3 bucket public access is blocked; photo objects are not intended to be public.
- API Gateway and FastAPI CORS configuration were adjusted to support the local frontend at `http://localhost:5173`.
- The Lambda package was rebuilt and deployed after the CORS and regional S3 endpoint changes.

### Added on 11 October 2026 (afternoon)

- **Production frontend:** https://main.d9c7imvqs8ukr.amplifyapp.com (AWS Amplify, branch `main`), using the deployed API with mock mode disabled. Details and smoke-test results: [Frontend deployment runbook](FRONTEND_DEPLOYMENT.md#10-deployment-record).
- **CORS:** API Gateway and FastAPI now allow `https://main.d9c7imvqs8ukr.amplifyapp.com` as well as `http://localhost:5173`. Preflight requests reach the Lambda through the `ANY /{proxy+}` route, so the FastAPI origin list must include every frontend origin, not only the API Gateway setting.
- **`PATCH /reports/{report_id}`** is deployed. Verified on the live API: status updated to `reviewed`, `verification_status` unchanged, unknown IDs return 404.
- **Server-side ward matching** is deployed. New reports get `ward_code` from their coordinates using `data/reference/mumbai_ward_boundaries.geojson` (verified: a report at 19.0287, 72.8566 was stored with `F/N`). Client-supplied ward codes are ignored; points outside every ward get `null`. Reports created before this change keep `ward_code: null`.
- **Lambda rollback points:** published version 1 (code before the PATCH/ward deploy) and version 2 (code before the Amplify CORS origin change). `$LATEST` runs the current code.
- **Demo data:** 12 simulated reports and a seed script are in `data/sample/` (see its README). They are not loaded into the production table unless the team runs the seed script for a demo.

These checks verify one successful end-to-end photo-report path. They do not prove that all error conditions, access-control scenarios, or operational requirements have been tested.

## Current functional areas

| Area | Current state | Qualification |
|---|---|---|
| Frontend | React/TypeScript/Vite application, deployed on Amplify | Production build verified in non-mock mode. Mock mode remains for local development. |
| API | FastAPI on Lambda behind API Gateway HTTP API | Health endpoint verified. |
| Weather/risk | Weather adapter and rule-based risk engine are present | Risk scores are heuristic and must be presented with provenance, freshness, scope, and limitations. |
| Historical exposure | Ward-level reference CSV and supporting documentation | Historical vulnerability context, not a live flood boundary or calibrated prediction. |
| Citizen reports | Create/list/status-update workflow and DynamoDB persistence; ward derived from coordinates | Report workflow status is separate from verification status. |
| Photo evidence | Presigned upload to private S3; server validates object before linking | Successful upload-and-report flow verified. |
| Responder dashboard | Report queue/status workflow prototype | No responder sign-in or backend authorization boundary yet. Do not treat as secure operational access. |
| Responder photo viewing | Not implemented | Requires authenticated/authorized API access before issuing short-lived download URLs. |

## Known security boundary

At this checkpoint, the responder dashboard explicitly has no sign-in. The report status-update API is also not protected by responder authentication/authorization. A UI-only login would not fix this: the backend must validate a trusted identity and role on each responder-only operation.

Until that work is complete:
- Do not describe responder operations as secure or production-ready.
- Do not expose permanent/public photo URLs.
- Keep the S3 bucket private.
- Implement and verify backend authorization before enabling responder-only presigned downloads.

## Next milestone — final sprint

**All times are IST (UTC+05:30). Hard code freeze: Sunday, 11 October 2026, 5:00 PM IST.** Implementation owners must hand off by 2:00 PM so the team has a dedicated integration window. From 5:00 PM onward, allow only release-blocking fixes, rollback, rehearsal, and demo preparation; do not add features.

The immediate final sprint is tracked in [Final sprint plan](FINAL_SPRINT_PLAN.md). It assigns:

1. **Laksh (3-hour cap):** inspect the existing risk engine and data first; run a small explainable ML experiment only if suitable labelled observations exist. Evaluate against a baseline, preserve the heuristic fallback, and do not claim predictive accuracy from synthetic data. If labels are not available, document model readiness instead of inventing labels.
2. **Manasvi (3-hour cap):** deploy the frontend to a live HTTPS URL, connect it to the deployed API, disable mock mode in production, verify report submission, and document the deployment.
3. **Mann:** own infrastructure approval, integration, production smoke tests, and demo freeze.
4. **Menaka:** update demo/video claims only after the new functionality is verified; target completion by Sunday 3:30 PM IST.

Deadlines: Laksh and Manasvi hand off by Sunday 2:00 PM IST; Mann leads integration/release checks from 2:00–5:00 PM; code freeze is Sunday 5:00 PM IST; 5:00 PM–midnight is contingency and demo preparation only. See the sprint plan for the detailed timeline. AWS access boundaries in the sprint plan are recommendations only. No IAM roles or policies were changed by this documentation update. Responder authentication remains a known security gap and should not be implied to exist.

## Demo guidance

Show the real successful citizen photo-report path, then show the current responder queue as a prototype. Do not imply responder authentication or secure responder-only access exists until implemented. Label simulated data, distinguish historical data from current weather-model inputs, and never present the heuristic score as a calibrated flood probability or official warning.
