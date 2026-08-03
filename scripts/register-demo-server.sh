#!/usr/bin/env bash
set -euo pipefail

API_PORT="${API_PORT:-8000}"

curl --fail --silent --show-error \
  -X POST "http://localhost:${API_PORT}/api/v1/servers" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "lab-hpe-sim-01",
    "redfish_url": "http://redfish-simulator:9000/redfish/v1/Systems/1"
  }' | python3 -m json.tool
