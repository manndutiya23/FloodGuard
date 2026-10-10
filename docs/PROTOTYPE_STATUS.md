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

These checks verify one successful end-to-end photo-report path. They do not prove that all error conditions, access-control scenarios, or operational requirements have been tested.

## Current functional areas

| Area | Current state | Qualification |
|---|---|---|
| Frontend | React/TypeScript/Vite application | Mock mode exists; use the configured non-mock mode to exercise deployed APIs. |
| API | FastAPI on Lambda behind API Gateway HTTP API | Health endpoint verified. |
| Weather/risk | Weather adapter and rule-based risk engine are present | Risk scores are heuristic and must be presented with provenance, freshness, scope, and limitations. |
| Historical exposure | Ward-level reference CSV and supporting documentation | Historical vulnerability context, not a live flood boundary or calibrated prediction. |
| Citizen reports | Create/list workflow and DynamoDB persistence | Report workflow status is separate from verification status. |
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

The immediate final sprint is tracked in [Final sprint plan](FINAL_SPRINT_PLAN.md). It assigns:

1. **Laksh (3-hour cap):** inspect the existing risk engine and data first; run a small explainable ML experiment only if suitable labelled observations exist. Evaluate against a baseline, preserve the heuristic fallback, and do not claim predictive accuracy from synthetic data. If labels are not available, document model readiness instead of inventing labels.
2. **Manasvi (3-hour cap):** deploy the frontend to a live HTTPS URL, connect it to the deployed API, disable mock mode in production, verify report submission, and document the deployment.
3. **Mann:** own infrastructure approval, integration, production smoke tests, and demo freeze.
4. **Menaka:** update demo/video claims only after the new functionality is verified.

AWS access boundaries in the sprint plan are recommendations only. No IAM roles or policies were changed by this documentation update. Responder authentication remains a known security gap and should not be implied to exist.

## Demo guidance

Show the real successful citizen photo-report path, then show the current responder queue as a prototype. Do not imply responder authentication or secure responder-only access exists until implemented. Label simulated data, distinguish historical data from current weather-model inputs, and never present the heuristic score as a calibrated flood probability or official warning.
