import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1").rstrip("/")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "5"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("serverops.collector")

app = FastAPI(
    title="ServerOps Collector",
    version="0.1.0",
    description="Reads synthetic Redfish endpoints and submits normalized observations.",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


def normalize_redfish(payload: dict[str, Any]) -> dict[str, Any]:
    overall_health = str(payload.get("Status", {}).get("Health", "Unknown"))
    disk_health = str(
        payload.get("StorageSummary", {}).get("Status", {}).get("Health", "Unknown")
    )
    return {
        "reachable": True,
        "overall_health": overall_health,
        "disk_health": disk_health,
    }


def changed_fields(previous: dict[str, Any], current: dict[str, Any]) -> list[str]:
    fields = ("reachable", "overall_health", "disk_health")
    return [field for field in fields if previous.get(field) != current.get(field)]


def scan_one(client: httpx.Client, server: dict[str, Any]) -> dict[str, Any]:
    collected_at = datetime.now(timezone.utc)
    raw_payload: dict[str, Any] = {}
    error: str | None = None

    try:
        response = client.get(server["redfish_url"])
        response.raise_for_status()
        raw_payload = response.json()
        normalized = normalize_redfish(raw_payload)
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Failed to scan server_id=%s: %s", server["id"], exc)
        normalized = {
            "reachable": False,
            "overall_health": "Unknown",
            "disk_health": server.get("disk_health", "Unknown"),
        }
        error = str(exc)[:1000]

    previous = {
        "reachable": server.get("reachable", False),
        "overall_health": server.get("overall_health", "Unknown"),
        "disk_health": server.get("disk_health", "Unknown"),
    }

    observation = {
        "server_id": server["id"],
        "source": "redfish",
        "collected_at": collected_at.isoformat(),
        "changed_fields": changed_fields(previous, normalized),
        "normalized": normalized,
        "raw_payload": raw_payload,
        "error": error,
    }

    ingest_response = client.post(f"{API_BASE_URL}/observations", json=observation)
    ingest_response.raise_for_status()
    return {
        "server_id": server["id"],
        "server_name": server["name"],
        "changed_fields": observation["changed_fields"],
        "result": ingest_response.json(),
    }


@app.post("/scan", tags=["scan"])
def scan_all_servers() -> dict[str, Any]:
    timeout = httpx.Timeout(REQUEST_TIMEOUT_SECONDS)
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(f"{API_BASE_URL}/servers")
            response.raise_for_status()
            servers = response.json()

            results = []
            failures = []
            for server in servers:
                try:
                    results.append(scan_one(client, server))
                except httpx.HTTPError as exc:
                    logger.exception("Observation submission failed for server_id=%s", server["id"])
                    failures.append({"server_id": server["id"], "error": str(exc)})
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="ServerOps API is unavailable") from exc

    return {
        "scanned": len(results),
        "failed": len(failures),
        "results": results,
        "failures": failures,
    }
