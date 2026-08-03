from api.app.services.incident_rules import (
    DISK_FAILURE,
    SERVER_UNREACHABLE,
    CurrentState,
    derive_server_status,
    desired_incident_types,
)


def test_healthy_server_has_no_desired_incidents() -> None:
    state = CurrentState(reachable=True, disk_health="OK")
    assert desired_incident_types(state) == set()


def test_disk_failure_creates_disk_incident() -> None:
    state = CurrentState(reachable=True, disk_health="Critical")
    assert desired_incident_types(state) == {DISK_FAILURE}


def test_unknown_disk_state_does_not_create_false_disk_failure() -> None:
    state = CurrentState(reachable=True, disk_health="Unknown")
    assert desired_incident_types(state) == set()


def test_unreachable_server_creates_only_unreachable_incident() -> None:
    state = CurrentState(reachable=False, disk_health="Critical")
    assert desired_incident_types(state) == {SERVER_UNREACHABLE}


def test_server_status_derivation() -> None:
    assert derive_server_status(reachable=True, overall_health="OK", disk_health="OK") == "HEALTHY"
    assert (
        derive_server_status(reachable=True, overall_health="Warning", disk_health="Critical")
        == "DEGRADED"
    )
    assert (
        derive_server_status(reachable=False, overall_health="Unknown", disk_health="Unknown")
        == "UNREACHABLE"
    )
