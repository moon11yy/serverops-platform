from copy import deepcopy
from threading import Lock
from typing import Any

from fastapi import FastAPI

app = FastAPI(
    title="Synthetic Redfish Simulator",
    version="0.1.0",
    description="A minimal Redfish-compatible source used only for the ServerOps lab.",
)

_state_lock = Lock()
_state: dict[str, Any] = {
    "Id": "1",
    "Name": "Synthetic HPE ProLiant",
    "Manufacturer": "Synthetic Lab",
    "Model": "ServerOps-SIM-01",
    "PowerState": "On",
    "Status": {"State": "Enabled", "Health": "OK"},
    "StorageSummary": {
        "Count": 2,
        "Status": {"State": "Enabled", "Health": "OK"},
    },
}


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/redfish/v1", tags=["redfish"])
def service_root() -> dict[str, Any]:
    return {
        "@odata.type": "#ServiceRoot.v1_15_0.ServiceRoot",
        "Id": "RootService",
        "Name": "Synthetic Redfish Service",
        "Systems": {"@odata.id": "/redfish/v1/Systems"},
    }


@app.get("/redfish/v1/Systems", tags=["redfish"])
def systems_collection() -> dict[str, Any]:
    return {
        "Members@odata.count": 1,
        "Members": [{"@odata.id": "/redfish/v1/Systems/1"}],
    }


@app.get("/redfish/v1/Systems/1", tags=["redfish"])
def computer_system() -> dict[str, Any]:
    with _state_lock:
        return deepcopy(_state)


@app.post("/control/disk-failure", tags=["simulation"])
def inject_disk_failure() -> dict[str, Any]:
    with _state_lock:
        _state["StorageSummary"]["Status"]["Health"] = "Critical"
        _state["Status"]["Health"] = "Warning"
        return {"message": "Synthetic disk failure enabled", "state": deepcopy(_state)}


@app.post("/control/disk-healthy", tags=["simulation"])
def repair_disk() -> dict[str, Any]:
    with _state_lock:
        _state["StorageSummary"]["Status"]["Health"] = "OK"
        _state["Status"]["Health"] = "OK"
        return {"message": "Synthetic disk health restored", "state": deepcopy(_state)}
