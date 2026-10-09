# FloodGuard Backend

Initial backend skeleton built with Python and FastAPI.

## Requirements

- Python 3.11 or newer
- pip

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

If PowerShell blocks virtual-environment activation, you can run the environment's Python directly instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --reload
```

## Verify the API

With the server running, open:

- Health endpoint: http://127.0.0.1:8000/health
- Interactive API docs: http://127.0.0.1:8000/docs

The health endpoint should return:

```json
{
  "status": "ok",
  "service": "floodguard-api"
}
```

A healthy response confirms that the API process is responding. It does not confirm that weather data, the risk engine, a database, or AWS deployment is available.

## Current scope

Implemented:
- FastAPI application
- `GET /health`

Not implemented yet:
- Ward baseline endpoint
- Open-Meteo weather adapter
- Risk-engine integration
- Incident-report endpoints or persistence
- AWS deployment

Keep secrets out of source control. The initial weather adapter is intended to use the selected provider's public API, subject to its usage terms.
