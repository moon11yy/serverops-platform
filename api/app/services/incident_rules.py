from dataclasses import dataclass


DISK_FAILURE = "DISK_FAILURE"
SERVER_UNREACHABLE = "SERVER_UNREACHABLE"

HEALTHY_VALUES = {"ok", "healthy", "enabled"}
DISK_FAILURE_VALUES = {"critical", "failed", "warning", "degraded"}


@dataclass(frozen=True)
class CurrentState:
    reachable: bool
    disk_health: str


def desired_incident_types(state: CurrentState) -> set[str]:
    desired: set[str] = set()

    if not state.reachable:
        desired.add(SERVER_UNREACHABLE)

    disk_health = state.disk_health.strip().lower()
    if state.reachable and disk_health in DISK_FAILURE_VALUES:
        desired.add(DISK_FAILURE)

    return desired


def derive_server_status(*, reachable: bool, overall_health: str, disk_health: str) -> str:
    if not reachable:
        return "UNREACHABLE"

    health_values = {overall_health.strip().lower(), disk_health.strip().lower()}
    if health_values.issubset(HEALTHY_VALUES):
        return "HEALTHY"

    return "DEGRADED"
