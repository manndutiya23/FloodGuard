# FloodGuard Backend

FastAPI application used for local development and the deployed AWS Lambda API.

## Requirements

- Python 3.11 or newer
- pip
- AWS credentials/configuration for local use of DynamoDB and S3-backed endpoints

## Run locally (Windows PowerShell)

From the repository root:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app:app --reload
```

If PowerShell blocks virtual-environment activation, run the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --reload
```

## Configuration

The deployed Lambda uses environment variables including:

- `REPORTS_TABLE_NAME`: DynamoDB report table name.
- `PHOTO_BUCKET_NAME`: private S3 bucket used for report photos.
- `AWS_REGION`: AWS region; the deployed environment uses `ap-south-1`.

The Lambda execution role needs only the permissions required for the configured DynamoDB and S3 operations. Do not commit credentials or real environment files. For local AWS-backed testing, use a least-privilege development identity and the appropriate environment variables.

## Verify the API

With the server running:

- Health endpoint: http://127.0.0.1:8000/health
- Interactive API docs: http://127.0.0.1:8000/docs

Expected health response:

```json
{
  "status": "ok",
  "service": "floodguard-api"
}
```

Health confirms the API process responds; it does not prove all data providers, AWS permissions, report persistence, or photo upload are healthy.

## Current implemented API areas

- `GET /health`
- `GET /wards`
- `GET /weather`
- `GET /risk`
- `GET /reports`
- `POST /reports`
- `POST /reports/photo-upload`
- `PATCH /reports/{report_id}`

The report/photo flow uses DynamoDB and private S3 storage in the deployed environment. Photo upload authorization is short-lived; the backend validates the uploaded object before linking it to a report.

`POST /reports` derives `ward_code` from the report's coordinates with `ward_lookup.py`, which reads `data/reference/mumbai_ward_boundaries.geojson` (positions are swapped from the file's `[lat, lng]` order at load time). Client-supplied ward codes are ignored. A point outside every ward, or a missing boundary file, gives `ward_code: null`; the report is still saved.

`PATCH /reports/{report_id}` changes only the workflow `status` (`new`, `reviewed`, `resolved`) and records `status_updated_at`. It never changes `verification_status`. Unknown IDs return 404.

## Deployment (AWS Lambda)

The deployed function is `floodguard-api` (Python 3.12, `ap-south-1`) behind the API Gateway HTTP API `floodguard-http-api` (`ANY /{proxy+}` route, `$default` stage). The Lambda handler is `lambda_handler.handler`, a small Mangum wrapper at the root of the package that imports `backend.app`. That wrapper is not in this repository.

The deployment package layout is:

```text
lambda_handler.py
backend/app.py, backend/risk_engine.py, backend/ward_lookup.py, backend/weather/
data/reference/floodguard_mumbai_ward_flood_exposure.csv
data/reference/mumbai_ward_boundaries.geojson
<Python dependencies built for Linux x86_64 at the package root>
```

When redeploying:

1. Publish the current code as a version first so you can roll back: `aws lambda publish-version --function-name floodguard-api`.
2. Build the package with the layout above. Include `ward_lookup.py` and the boundary GeoJSON, otherwise new reports get `ward_code: null`.
3. Upload with `aws lambda update-function-code --function-name floodguard-api --zip-file fileb://<package>.zip` and wait for `LastUpdateStatus: Successful`.
4. Smoke test `/health`, `/wards`, `/risk`, `/reports`, a CORS preflight from each frontend origin, and a harmless test report (delete it afterwards).

**CORS:** preflight `OPTIONS` requests reach FastAPI through the catch-all route, so a new frontend origin must be added to both the `CORSMiddleware` list in `app.py` **and** the API Gateway CORS configuration. Current origins: `http://localhost:5173` and `https://main.d9c7imvqs8ukr.amplifyapp.com`.

Published rollback versions (11 October 2026): `1` = before the PATCH/ward-matching deploy, `2` = before the Amplify CORS origin change.

## Demo data

`seed_demo_reports.py` loads or removes the 12 simulated reports in `data/sample/demo_reports.json`. It is a dry run unless `--apply` is passed, and `--remove` deletes only `demo-*` IDs. See `data/sample/README.md`.

## Security status

**Responder authentication/authorization is not implemented yet.** The current responder dashboard and report status update endpoint are prototype functionality, not secure responder-only access. Do not add responder-only photo download links until backend authentication and authorization are enforced. See [prototype status](../docs/PROTOTYPE_STATUS.md).

## Tests

Run backend tests from the repository root using the project's test dependencies:

```powershell
python -m pytest backend/tests
```

Tests that require network access or configured AWS resources may need separate setup; do not infer deployed AWS behavior from unit tests alone.
