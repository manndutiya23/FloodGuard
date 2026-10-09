"""FloodGuard API application.

This is the initial local backend skeleton. Feature endpoints will be added
after the shared API and risk-engine contracts are implemented.
"""

from fastapi import FastAPI

app = FastAPI(
    title="FloodGuard API",
    description="API for Mumbai hyperlocal flood intelligence.",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Confirm that the API process is responding."""
    return {
        "status": "ok",
        "service": "floodguard-api",
    }
