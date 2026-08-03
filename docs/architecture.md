# MVP Architecture

```mermaid
sequenceDiagram
    actor Operator
    participant Collector
    participant Redfish as Redfish Simulator
    participant API as FastAPI
    participant PG as PostgreSQL
    participant Mongo as MongoDB

    Operator->>Collector: POST /scan
    Collector->>API: GET /servers
    API->>PG: Read inventory/current state
    PG-->>API: Servers
    API-->>Collector: Servers
    Collector->>Redfish: GET /redfish/v1/Systems/1
    Redfish-->>Collector: Raw Redfish JSON
    Collector->>Collector: Normalize and detect changed fields
    Collector->>API: POST /observations
    API->>Mongo: Insert raw observation
    API->>PG: Update current state
    API->>PG: Reconcile incidents
    API->>PG: Write audit log
    API-->>Collector: Reconciliation result
    Collector-->>Operator: Scan summary
```

## Boundaries

- The collector is read-only toward monitored systems.
- The API owns business rules and database writes.
- PostgreSQL owns current operational truth.
- MongoDB preserves source evidence and flexible historical payloads.
- The simulator is isolated synthetic infrastructure.
