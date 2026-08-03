import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pymongo.errors import PyMongoError
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.models import AuditLog, Incident, Server
from app.mongo import mongo_client, mongo_db
from app.schemas import (
    AuditLogRead,
    IncidentRead,
    ObservationCreate,
    ObservationResult,
    ServerCreate,
    ServerRead,
)
from app.services.incident_rules import derive_server_status
from app.services.incident_service import reconcile_incidents

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("serverops.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    mongo_db.raw_observations.create_index([("server_id", 1), ("collected_at", -1)])
    logger.info("Database schema and MongoDB indexes are ready")
    yield
    mongo_client.close()


app = FastAPI(
    title="ServerOps Platform API",
    version="0.1.0",
    description="Inventory, observations, incidents, and audit records for a synthetic lab.",
    lifespan=lifespan,
)


@app.get("/health", tags=["system"])
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
        mongo_client.admin.command("ping")
    except Exception as exc:  # health endpoint must report dependency failures
        logger.exception("Dependency health check failed")
        raise HTTPException(status_code=503, detail="A database dependency is unavailable") from exc
    return {"status": "ok"}


@app.post(
    "/api/v1/servers",
    response_model=ServerRead,
    status_code=status.HTTP_201_CREATED,
    tags=["servers"],
)
def create_server(payload: ServerCreate, db: Session = Depends(get_db)) -> Server:
    server = Server(name=payload.name, redfish_url=str(payload.redfish_url))
    db.add(server)
    try:
        db.flush()
        db.add(
            AuditLog(
                actor="api",
                action="SERVER_REGISTERED",
                entity_type="server",
                entity_id=str(server.id),
                details={"name": server.name, "redfish_url": server.redfish_url},
            )
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Server name or Redfish URL already exists") from exc
    db.refresh(server)
    return server


@app.get("/api/v1/servers", response_model=list[ServerRead], tags=["servers"])
def list_servers(db: Session = Depends(get_db)) -> list[Server]:
    return list(db.scalars(select(Server).order_by(Server.id)))


@app.get("/api/v1/servers/{server_id}", response_model=ServerRead, tags=["servers"])
def get_server(server_id: int, db: Session = Depends(get_db)) -> Server:
    server = db.get(Server, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


@app.post(
    "/api/v1/observations",
    response_model=ObservationResult,
    tags=["collector"],
)
def ingest_observation(
    payload: ObservationCreate,
    db: Session = Depends(get_db),
) -> ObservationResult:
    server = db.get(Server, payload.server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")

    raw_document = {
        "server_id": payload.server_id,
        "source": payload.source,
        "collected_at": payload.collected_at,
        "received_at": datetime.now(timezone.utc),
        "changed_fields": payload.changed_fields,
        "normalized": payload.normalized.model_dump(),
        "raw_payload": payload.raw_payload,
        "error": payload.error,
    }

    try:
        mongo_db.raw_observations.insert_one(raw_document)
    except PyMongoError as exc:
        logger.exception("Failed to persist raw observation")
        raise HTTPException(status_code=503, detail="Raw observation store is unavailable") from exc

    previous_state = {
        "status": server.status,
        "reachable": server.reachable,
        "overall_health": server.overall_health,
        "disk_health": server.disk_health,
    }

    server.reachable = payload.normalized.reachable
    server.overall_health = payload.normalized.overall_health
    server.disk_health = payload.normalized.disk_health
    server.status = derive_server_status(
        reachable=server.reachable,
        overall_health=server.overall_health,
        disk_health=server.disk_health,
    )
    if server.reachable:
        server.last_seen_at = payload.collected_at

    created, resolved = reconcile_incidents(db, server)
    db.add(
        AuditLog(
            actor="collector",
            action="OBSERVATION_INGESTED",
            entity_type="server",
            entity_id=str(server.id),
            details={
                "changed_fields": payload.changed_fields,
                "previous_state": previous_state,
                "current_state": {
                    "status": server.status,
                    "reachable": server.reachable,
                    "overall_health": server.overall_health,
                    "disk_health": server.disk_health,
                },
            },
        )
    )
    db.commit()

    return ObservationResult(
        server_id=server.id,
        server_status=server.status,
        created_incident_types=created,
        resolved_incident_types=resolved,
    )


@app.get("/api/v1/incidents", response_model=list[IncidentRead], tags=["incidents"])
def list_incidents(
    incident_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[Incident]:
    statement = select(Incident).order_by(Incident.opened_at.desc())
    if incident_status:
        normalized_status = incident_status.upper()
        if normalized_status not in {"OPEN", "RESOLVED"}:
            raise HTTPException(status_code=422, detail="status must be OPEN or RESOLVED")
        statement = statement.where(Incident.status == normalized_status)
    return list(db.scalars(statement))


@app.get("/api/v1/audit-logs", response_model=list[AuditLogRead], tags=["audit"])
def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[AuditLog]:
    return list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)))
