from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RobotState = Literal["idle", "moving", "error"]


class TelemetryIn(BaseModel):
    battery: float = Field(ge=0, le=100, description="Battery level in percent")
    x: float
    y: float
    state: RobotState


class Telemetry(TelemetryIn):
    robot_id: str
    timestamp: datetime


class RobotSummary(BaseModel):
    robot_id: str
    state: RobotState
    timestamp: datetime
