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

## Security status

**Responder authentication/authorization is not implemented yet.** The current responder dashboard and report status update endpoint are prototype functionality, not secure responder-only access. Do not add responder-only photo download links until backend authentication and authorization are enforced. See [prototype status](../docs/PROTOTYPE_STATUS.md).

## Tests

Run backend tests from the repository root using the project's test dependencies:

```powershell
python -m pytest backend/tests
```

Tests that require network access or configured AWS resources may need separate setup; do not infer deployed AWS behavior from unit tests alone.
