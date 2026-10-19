import os
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, status

from app.models import RobotSummary, Telemetry, TelemetryIn

APP_VERSION = os.getenv("APP_VERSION", "dev")

app = FastAPI(title="Robot Telemetry API", version=APP_VERSION)

# Latest telemetry per robot. In-memory only: resets when the process restarts.
store: dict[str, Telemetry] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": APP_VERSION}


@app.post(
    "/robots/{robot_id}/telemetry",
    status_code=status.HTTP_201_CREATED,
    response_model=Telemetry,
)
def report_telemetry(robot_id: str, payload: TelemetryIn) -> Telemetry:
    record = Telemetry(robot_id=robot_id, timestamp=datetime.now(UTC), **payload.model_dump())
    store[robot_id] = record
    return record


@app.get("/robots/{robot_id}", response_model=Telemetry)
def get_robot(robot_id: str) -> Telemetry:
    record = store.get(robot_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Robot '{robot_id}' not found")
    return record


@app.get("/robots", response_model=list[RobotSummary])
def list_robots() -> list[RobotSummary]:
    return [
        RobotSummary(robot_id=r.robot_id, state=r.state, timestamp=r.timestamp)
        for r in store.values()
    ]
