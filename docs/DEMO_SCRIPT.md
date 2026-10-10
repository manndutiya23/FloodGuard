# FloodGuard demo script

**Target length:** 90–120 seconds  
**Mode:** Use the deployed API and real persisted report flow. Do not rely on a mock report for the steps described as live.

## Before recording

- Confirm the frontend is configured for the intended API and mock mode is disabled.
- Open the Mumbai map/dashboard and confirm the API health endpoint responds.
- Use a prepared, harmless JPEG/PNG/WebP image under 5 MiB.
- Ensure the responder dashboard is presented honestly as a prototype; responder sign-in and backend authorization are not implemented yet.
- Do not expose presigned URLs, credentials, environment files, or personal information in the recording.

## Suggested narration and actions

### 1. Problem and context (0:00–0:15)

“Flooding in Mumbai can be highly localized. FloodGuard brings together historical ward exposure, available environmental signals, and citizen observations so people can understand context and responders can see reports that may need attention.”

Show the map/ward context. Identify historical exposure as historical data, and label weather-model forecasts as forecasts rather than direct rain-gauge measurements.

### 2. Explain the assessment (0:15–0:35)

Show the current risk view and its contributing reasons, source/data status, and timestamps where available.

“The score is a transparent prototype heuristic, not a calibrated probability or an official flood warning. FloodGuard surfaces the available evidence and its limitations rather than pretending uncertainty does not exist.”

Do not invent a live event or claim that a ward-specific signal exists if the deployed view does not support it.

### 3. Submit a citizen report with photo (0:35–0:55)

Open the citizen report form, choose a location/category, add a short factual description, attach the prepared image, and submit once.

“The photo is uploaded directly to private S3 using short-lived upload authorization. The backend checks the uploaded object before linking it to the saved report.”

Show the actual confirmation and report reference. The tested flow has returned S3 `204` and report creation `201`.

### 4. Show the report workflow (0:55–1:15)

Open the report list/responder dashboard and find the newly created report. Show its workflow and verification status accurately.

“New reports are unverified until reviewed. Marking a report reviewed is a workflow action; it does not automatically certify the report as verified.”

**Security disclosure:** the current responder dashboard has no sign-in and its status-update endpoint is not protected by responder authorization. Present this as prototype workflow only. Do not claim secure responder-only access or demonstrate sensitive data.

### 5. Close (1:15–1:30)

“FloodGuard's current prototype connects ward context, environmental signals, and community reports, including private photo evidence. The next milestone is responder authentication and authorization, followed by secure, short-lived evidence viewing.”

## Recording checklist

- [ ] Main workflow succeeds in one take.
- [ ] Real data and simulated data are clearly distinguished.
- [ ] Historical exposure is not described as current flood conditions.
- [ ] Forecast/model values are not called direct observations.
- [ ] Heuristic scores are not described as calibrated probabilities.
- [ ] No secrets or presigned URLs are visible.
- [ ] No claim of responder authentication or secure photo viewing is made.
