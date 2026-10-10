# Report API Contract Finalization

**Status:** Approved by the project frontend stakeholder; share with the team for implementation alignment. This addendum supplements `docs/API_CONTRACT.md`. It does not replace the previously agreed risk-scoring decisions in `docs/RISK_SCORING_DECISIONS.md`.

## 1. Decisions

- **Report pagination:** Cursor pagination, newest first, with a deterministic timestamp tie-breaker.
- **Ward assignment:** The backend derives the authoritative ward from coordinates and boundary geometry. A client-supplied ward hint is not trusted. If no reliable match exists, use `ward_code: null`.
- **Responder access:** Amazon Cognito authentication plus backend authorization checks for the responder role. Authentication alone is not authorization.
- **Risk evaluation:** Calculate on request for the first cloud milestone; add scheduled AWS evaluation later. Do not imply that report submission changes a risk score until report-to-risk integration is implemented.
- **Demo data:** Simulated reports are allowed for the hackathon demonstration and must be clearly labelled as simulated in the UI and narration. The backend controls the simulation flag; a public client cannot freely mark arbitrary reports as simulated or verified.
- **Optional photo:** One photo per report, maximum 5 MB, JPEG/PNG/WebP. Upload directly to private S3 using a short-lived presigned upload authorization. Store the object key and validated metadata with the report in DynamoDB. Responders receive a short-lived viewing URL only after authorization.

The existing scoring agreement remains unchanged. See `docs/RISK_SCORING_DECISIONS.md` for the agreed formula and parameters.

## 2. `GET /reports` — cursor pagination

Optional query parameters:
- `limit`: page size, capped by a server-side maximum.
- `cursor`: opaque cursor returned by the previous response.
- `status`: optional workflow-status filter.
- `ward_code`: optional filter for reliably assigned wards.

Response shape:

```json
{
  "data": [],
  "pagination": {
    "next_cursor": "opaque-cursor-or-null",
    "has_more": false
  }
}
```

Ordering is newest first with a deterministic tie-breaker (for example, report ID). The cursor is opaque and must not expose arbitrary internal database keys. Keep filters consistent while following a cursor. Cursor semantics must be implemented against the chosen DynamoDB access pattern; do not emulate cursor pagination with unbounded full-table scans.

## 3. `POST /reports` — create a report

The client supplies:
- `latitude`
- `longitude`
- `category`
- `description` (maximum 280 characters)
- optional `photo_upload_id`

The server generates the report ID and timestamp and controls initial workflow/verification state. Initial values are `status: "new"` and `verification_status: "unverified"`. The server derives `ward_code` from coordinates. A client ward hint, if accepted for convenience, is advisory only.

Example request:

```json
{
  "latitude": 19.076,
  "longitude": 72.8777,
  "category": "waterlogging",
  "description": "Water accumulating near Gate 2",
  "photo_upload_id": "upload-id-from-photo-flow"
}
```

The response uses the existing `{ "data": { ... } }` envelope and includes `report_id`, derived `ward_code` (possibly null), `status`, `verification_status`, `reported_at`, `is_simulated`, and photo availability/metadata where applicable. The response must not expose a permanent public S3 URL.

A public citizen request cannot set `verification_status: "verified"`. Simulation status is determined by backend-controlled demo configuration or an authorized demo path, not trusted from arbitrary request JSON. A successful report submission does not itself prove that flooding was observed.

## 4. Optional photo upload flow

### `POST /reports/photo-upload`

Requests authorization to upload one photo. The backend validates content type and issues a short-lived presigned S3 upload URL with a server-generated object key and the required upload headers/fields.

Initial constraints:
- At most one photo per report.
- Maximum file size: 5 MB.
- Allowed formats: JPEG, PNG, WebP.
- Upload URL lifetime: approximately five minutes.
- S3 bucket and objects remain private.

The frontend uploads the binary directly to S3 rather than proxying it through API Gateway. The backend tracks the pending upload using an upload ID.

After upload, the client includes `photo_upload_id` in `POST /reports`. The backend verifies the pending upload belongs to the intended flow, has not expired or already been consumed, and that the object exists and conforms to allowed metadata/size constraints before linking it to the report. An absent photo must not block a report. Invalid or incomplete uploads must not be represented as an available photo.

### `GET /reports/{report_id}/photo-url`

Requires a Cognito-authenticated responder whose role is authorized to view the report. The backend checks authorization and then returns a short-lived viewing URL for the private S3 object. Do not make report photos publicly readable.

## 5. `PATCH /reports/{report_id}` — responder workflow

Requires responder authorization. Supports the existing workflow values `new`, `reviewed`, and `resolved`. Updating workflow status does not automatically change verification status. Verification must remain a separate action/field and cannot be self-assigned by a citizen.

Until the Cognito role check is enforced by the backend, this endpoint must not be described as secure responder access.

## 6. Risk evaluation and simulated data

The initial cloud milestone uses on-request risk calculation. Scheduled AWS evaluation (for example, EventBridge-triggered evaluation) is a later milestone.

Do not claim that a report affects a live risk score until the live `/risk` path actually loads persisted reports and passes eligible reports to the risk engine. Simulated and genuine reports must remain distinguishable. Any score using simulated inputs must be labelled simulated; simulated reports must not be presented in the demo as genuine citizen submissions.

## 7. Errors and security

Use the shared error shape from `docs/API_CONTRACT.md`:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid fields."
  },
  "request_id": "example-request-id"
}
```

The `request_id` may be omitted when unavailable. Do not return stack traces, credentials, permanent public object URLs, or sensitive infrastructure details. Validate coordinates, category, description length, upload ownership, content type and size, cursor input, and workflow transitions. Apply appropriate request throttling/abuse controls to public report submission and upload authorization.

## 8. First end-to-end acceptance test

1. Load the dashboard with visibly labelled simulated demo reports.
2. Submit a report without a photo.
3. Submit a report with an allowed photo.
4. Refresh the page and confirm both reports persist.
5. Browse the queue using cursor pagination without duplicate or skipped items in a stable test dataset.
6. Sign in as a responder through Cognito, open a report photo through an authorized short-lived URL, and update a report's workflow status.
7. Confirm unauthenticated users cannot update workflow status or request photo viewing URLs.
8. Confirm a citizen cannot mark a report verified.
9. Confirm the UI and demo narration identify simulated reports clearly.
10. Confirm the application does not claim report-driven risk changes until report-to-risk integration is actually implemented.

## 9. Implementation notes

This document records the contract target; it is not evidence that the endpoints, AWS resources, or authorization are already implemented. Frontend, backend, and AWS implementation should agree on exact request/response fields before coding against this addendum. The five-megabyte limit, one-photo limit, allowed formats, and approximate URL lifetime are proposed implementation defaults for the hackathon and should be kept consistent across client and server validation.
