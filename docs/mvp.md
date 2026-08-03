# Phase 1: MVP Definition

## Goal

Prove an end-to-end incident lifecycle using one simulated server and one fault type.

## Included

- FastAPI backend
- Python collector
- PostgreSQL current-state store
- MongoDB raw-observation store
- Minimal Redfish-compatible simulator
- Docker Compose
- Disk-failure incident rule
- Automatic incident resolution
- Audit log
- Swagger documentation
- Unit tests for incident rules

## Excluded

- Authentication and authorization
- Dashboard
- Prometheus and Grafana
- Kubernetes
- CI/CD
- Terraform
- Argo CD
- Real hardware management actions
- Automatic destructive remediation

## Definition of done

1. `docker compose up --build -d` starts all services.
2. A server is registered through `POST /api/v1/servers`.
3. A collector scan succeeds.
4. The raw document is written to MongoDB.
5. The current state is written to PostgreSQL.
6. Disk health changes from `OK` to `Critical`.
7. Exactly one active incident is created.
8. Disk health changes back to `OK`.
9. The incident is resolved.
10. Audit records exist for every state-changing action.
