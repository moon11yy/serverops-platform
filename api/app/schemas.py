from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ServerCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120, pattern=r"^[a-zA-Z0-9._-]+$")
    redfish_url: HttpUrl


class ServerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    redfish_url: str
    status: str
    reachable: bool
    overall_health: str
    disk_health: str
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime


class NormalizedState(BaseModel):
    reachable: bool
    overall_health: str = "Unknown"
    disk_health: str = "Unknown"


class ObservationCreate(BaseModel):
    server_id: int
    source: str = Field(default="redfish", max_length=50)
    collected_at: datetime
    changed_fields: list[str] = Field(default_factory=list)
    normalized: NormalizedState
    raw_payload: dict[str, Any]
    error: str | None = Field(default=None, max_length=1000)


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    server_id: int
    incident_type: str
    title: str
    severity: str
    status: str
    details: dict[str, Any]
    opened_at: datetime
    resolved_at: datetime | None


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor: str
    action: str
    entity_type: str
    entity_id: str
    details: dict[str, Any]
    created_at: datetime


class ObservationResult(BaseModel):
    server_id: int
    server_status: str
    created_incident_types: list[str]
    resolved_incident_types: list[str]
