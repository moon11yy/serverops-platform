#!/usr/bin/env bash
set -euo pipefail

API_PORT="${API_PORT:-8000}"
COLLECTOR_PORT="${COLLECTOR_PORT:-8001}"
SIMULATOR_PORT="${SIMULATOR_PORT:-9000}"

pretty() { python3 -m json.tool; }

echo "1. Registering the synthetic server"
response_file="$(mktemp)"
http_code="$(curl --silent --output "$response_file" --write-out '%{http_code}' \
  -X POST "http://localhost:${API_PORT}/api/v1/servers" \
  -H 'Content-Type: application/json' \
  -d '{"name":"lab-hpe-sim-01","redfish_url":"http://redfish-simulator:9000/redfish/v1/Systems/1"}')"
if [[ "$http_code" == "201" || "$http_code" == "409" ]]; then
  cat "$response_file" | pretty
else
  cat "$response_file" >&2
  rm -f "$response_file"
  exit 1
fi
rm -f "$response_file"

echo
echo "2. Healthy scan"
curl --fail --silent --show-error -X POST "http://localhost:${COLLECTOR_PORT}/scan" | pretty

echo
echo "3. Injecting disk failure"
curl --fail --silent --show-error -X POST "http://localhost:${SIMULATOR_PORT}/control/disk-failure" | pretty

echo
echo "4. Failed scan: one incident should open"
curl --fail --silent --show-error -X POST "http://localhost:${COLLECTOR_PORT}/scan" | pretty

echo
echo "5. Repeating failed scan: no duplicate incident should open"
curl --fail --silent --show-error -X POST "http://localhost:${COLLECTOR_PORT}/scan" | pretty

echo
echo "6. Active incident list"
curl --fail --silent --show-error "http://localhost:${API_PORT}/api/v1/incidents?status=OPEN" | pretty

echo
echo "7. Repairing disk"
curl --fail --silent --show-error -X POST "http://localhost:${SIMULATOR_PORT}/control/disk-healthy" | pretty

echo
echo "8. Healthy scan: incident should resolve"
curl --fail --silent --show-error -X POST "http://localhost:${COLLECTOR_PORT}/scan" | pretty

echo
echo "9. Incident history"
curl --fail --silent --show-error "http://localhost:${API_PORT}/api/v1/incidents" | pretty

echo
echo "10. Recent audit records"
curl --fail --silent --show-error "http://localhost:${API_PORT}/api/v1/audit-logs?limit=20" | pretty
