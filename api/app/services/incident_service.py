from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, Incident, Server
from app.services.incident_rules import DISK_FAILURE, SERVER_UNREACHABLE, CurrentState, desired_incident_types


INCIDENT_TITLES = {
    DISK_FAILURE: "Disk health is not OK",
    SERVER_UNREACHABLE: "Server is unreachable",
}

INCIDENT_SEVERITIES = {
    DISK_FAILURE: "HIGH",
    SERVER_UNREACHABLE: "CRITICAL",
}


def reconcile_incidents(db: Session, server: Server) -> tuple[list[str], list[str]]:
    desired = desired_incident_types(
        CurrentState(reachable=server.reachable, disk_health=server.disk_health)
    )

    open_incidents = list(
        db.scalars(
            select(Incident).where(
                Incident.server_id == server.id,
                Incident.status == "OPEN",
            )
        )
    )
    open_by_type = {incident.incident_type: incident for incident in open_incidents}

    created: list[str] = []
    resolved: list[str] = []

    for incident_type in sorted(desired - open_by_type.keys()):
        incident = Incident(
            server_id=server.id,
            incident_type=incident_type,
            title=INCIDENT_TITLES[incident_type],
            severity=INCIDENT_SEVERITIES[incident_type],
            status="OPEN",
            details={
                "server_name": server.name,
                "disk_health": server.disk_health,
                "reachable": server.reachable,
            },
        )
        db.add(incident)
        db.flush()
        db.add(
            AuditLog(
                actor="incident-engine",
                action="INCIDENT_OPENED",
                entity_type="incident",
                entity_id=str(incident.id),
                details={"incident_type": incident_type, "server_id": server.id},
            )
        )
        created.append(incident_type)

    for incident_type in sorted(open_by_type.keys() - desired):
        incident = open_by_type[incident_type]
        incident.status = "RESOLVED"
        incident.resolved_at = datetime.now(timezone.utc)
        db.add(
            AuditLog(
                actor="incident-engine",
                action="INCIDENT_RESOLVED",
                entity_type="incident",
                entity_id=str(incident.id),
                details={"incident_type": incident_type, "server_id": server.id},
            )
        )
        resolved.append(incident_type)

    return created, resolved
