# IoTFlow Architecture - PostgreSQL for Telemetry Storage

## System Architecture with PostgreSQL Replacing IoTDB

This document outlines the architecture where PostgreSQL handles both metadata and telemetry data, replacing Apache IoTDB.

---

## High-Level Architecture

```mermaid
graph TB
    subgraph "IoT Devices"
        D1[Device 1<br/>Sensors]
        D2[Device 2<br/>Actuators]
        D3[Device N<br/>Gateways]
    end

    subgraph "Communication Protocols"
        HTTP[HTTP/REST API<br/>Port 5000]
        MQTT[MQTT Broker<br/>Mosquitto<br/>Port 1883]
    end

    subgraph "Application Layer"
        FLASK[Flask Application<br/>Gunicorn Workers]
        AUTH[Authentication<br/>Middleware]
        ROUTES[API Routes<br/>Devices/Telemetry/Admin]
    end

    subgraph "Data Storage Layer"
        PG[(PostgreSQL<br/>Metadata + Telemetry)]
        REDIS[(Redis Cache<br/>Device Status)]
    end

    subgraph "Monitoring & Metrics"
        PROM[Prometheus<br/>Metrics Collection]
        GRAF[Grafana<br/>Dashboards]
        NODE[Node Exporter<br/>System Metrics]
    end

    D1 -->|HTTP POST| HTTP
    D2 -->|MQTT Publish| MQTT
    D3 -->|HTTP/MQTT| HTTP
    D3 -->|HTTP/MQTT| MQTT

    HTTP --> FLASK
    MQTT --> FLASK

    FLASK --> AUTH
    AUTH --> ROUTES
    ROUTES --> PG
    ROUTES --> REDIS

    FLASK --> PROM
    PROM --> GRAF
    NODE --> PROM

    style PG fill:#4169E1,stroke:#000,stroke-width:3px,color:#fff
    style FLASK fill:#90EE90,stroke:#000,stroke-width:2px
    style MQTT fill:#FF6B6B,stroke:#000,stroke-width:2px
    style REDIS fill:#DC143C,stroke:#000,stroke-width:2px,color:#fff
```

---

## Detailed Component Architecture

```mermaid
graph LR
    subgraph "Client Layer"
        DEV[IoT Devices]
        WEB[Web Dashboard]
        MOB[Mobile Apps]
    end

    subgraph "API Gateway"
        LB[Load Balancer<br/>Nginx/HAProxy]
    end

    subgraph "Application Services"
        F1[Flask Instance 1]
        F2[Flask Instance 2]
        F3[Flask Instance N]
    end

    subgraph "Business Logic"
        DM[Device Manager]
        TM[Telemetry Manager]
        AM[Admin Manager]
        MM[MQTT Manager]
    end

    subgraph "Data Access Layer"
        ORM[SQLAlchemy ORM]
        CACHE[Redis Client]
    end

    subgraph "Storage"
        PG[(PostgreSQL<br/>Primary Database)]
        REDIS[(Redis<br/>Cache Layer)]
    end

    DEV --> LB
    WEB --> LB
    MOB --> LB

    LB --> F1
    LB --> F2
    LB --> F3

    F1 --> DM
    F1 --> TM
    F2 --> DM
    F2 --> TM
    F3 --> AM
    F3 --> MM

    DM --> ORM
    TM --> ORM
    AM --> ORM
    MM --> ORM

    DM --> CACHE
    TM --> CACHE

    ORM --> PG
    CACHE --> REDIS

    style PG fill:#4169E1,stroke:#000,stroke-width:3px,color:#fff
    style REDIS fill:#DC143C,stroke:#000,stroke-width:2px,color:#fff
```

---

## PostgreSQL Database Schema with Telemetry

```mermaid
erDiagram
    USERS ||--o{ DEVICES : owns
    USERS ||--o{ CHARTS : creates
    DEVICES ||--o{ DEVICE_AUTH : has
    DEVICES ||--o{ DEVICE_CONFIGURATIONS : has
    DEVICES ||--o{ DEVICE_CONTROL : receives
    DEVICES ||--o{ TELEMETRY_DATA : generates
    DEVICES ||--o{ CHART_DEVICES : displayed_in
    CHARTS ||--o{ CHART_DEVICES : contains
    CHARTS ||--o{ CHART_MEASUREMENTS : defines

    USERS {
        int id PK
        string user_id UK
        string username UK
        string email UK
        string password_hash
        boolean is_active
        boolean is_admin
        timestamp created_at
        timestamp updated_at
        timestamp last_login
    }

    DEVICES {
        int id PK
        string name
        text description
        string device_type
        string api_key UK
        string status
        string location
        string firmware_version
        string hardware_version
        int user_id FK
        timestamp created_at
        timestamp updated_at
        timestamp last_seen
    }

    DEVICE_AUTH {
        int id PK
        int device_id FK
        string api_key_hash
        boolean is_active
        timestamp expires_at
        timestamp created_at
        timestamp last_used
        int usage_count
    }

    DEVICE_CONFIGURATIONS {
        int id PK
        int device_id FK
        string config_key
        text config_value
        string data_type
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    DEVICE_CONTROL {
        int id PK
        int device_id FK
        string command
        json parameters
        string status
        timestamp created_at
        timestamp updated_at
    }

    TELEMETRY_DATA {
        bigint id PK
        int device_id FK
        int user_id FK
        timestamp timestamp
        string measurement_name
        float numeric_value
        string text_value
        boolean boolean_value
        json json_value
        json metadata
        timestamp created_at
    }

    CHARTS {
        string id PK
        string name
        string title
        text description
        string type
        int user_id FK
        string time_range
        int refresh_interval
        string aggregation
        string group_by
        json appearance_config
        timestamp created_at
        timestamp updated_at
        boolean is_active
    }

    CHART_DEVICES {
        int id PK
        string chart_id FK
        int device_id FK
        timestamp created_at
    }

    CHART_MEASUREMENTS {
        int id PK
        string chart_id FK
        string measurement_name
        string display_name
        string color
        timestamp created_at
    }
```

---

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant Device
    participant MQTT
    participant Flask
    participant Auth
    participant TelemetryService
    participant PostgreSQL
    participant Redis
    participant Prometheus

    Device->>MQTT: Publish telemetry
    MQTT->>Flask: Forward message
    Flask->>Auth: Validate API key
    Auth->>PostgreSQL: Check device credentials
    PostgreSQL-->>Auth: Device validated
    Auth-->>Flask: Authentication OK
    
    Flask->>TelemetryService: Process telemetry
    TelemetryService->>PostgreSQL: INSERT telemetry_data
    PostgreSQL-->>TelemetryService: Data stored
    
    TelemetryService->>Redis: Update device status
    Redis-->>TelemetryService: Status cached
    
    TelemetryService->>Prometheus: Increment metrics
    Prometheus-->>TelemetryService: Metrics recorded
    
    TelemetryService-->>Flask: Success response
    Flask-->>Device: 201 Created
```

---

## Telemetry Query Flow

```mermaid
sequenceDiagram
    participant Client
    participant Flask
    participant Auth
    participant TelemetryService
    participant PostgreSQL
    participant Redis

    Client->>Flask: GET /api/v1/telemetry/{device_id}
    Flask->>Auth: Validate API key
    Auth->>Redis: Check cached auth
    
    alt Cache Hit
        Redis-->>Auth: Cached credentials
    else Cache Miss
        Auth->>PostgreSQL: Query device
        PostgreSQL-->>Auth: Device data
        Auth->>Redis: Cache credentials
    end
    
    Auth-->>Flask: Authorized
    
    Flask->>TelemetryService: Query telemetry
    TelemetryService->>PostgreSQL: SELECT with time range
    Note over PostgreSQL: Uses indexes on<br/>device_id, timestamp
    PostgreSQL-->>TelemetryService: Telemetry records
    
    TelemetryService->>TelemetryService: Format response
    TelemetryService-->>Flask: Formatted data
    Flask-->>Client: 200 OK + JSON data
```

---

## PostgreSQL Telemetry Table Design

```mermaid
graph TB
    subgraph "Telemetry Storage Strategy"
        MAIN[Main Telemetry Table<br/>telemetry_data]
        
        subgraph "Partitioning Strategy"
            P1[Partition by Time<br/>Monthly/Weekly]
            P2[Partition by Device<br/>High-volume devices]
            P3[Hybrid Partitioning<br/>Time + Device]
        end
        
        subgraph "Indexing Strategy"
            I1[Index: device_id + timestamp]
            I2[Index: user_id + timestamp]
            I3[Index: measurement_name]
            I4[Index: timestamp DESC]
        end
        
        subgraph "Data Types"
            T1[Numeric: DOUBLE PRECISION]
            T2[Text: TEXT]
            T3[Boolean: BOOLEAN]
            T4[Complex: JSONB]
        end
        
        MAIN --> P1
        MAIN --> P2
        MAIN --> P3
        
        MAIN --> I1
        MAIN --> I2
        MAIN --> I3
        MAIN --> I4
        
        MAIN --> T1
        MAIN --> T2
        MAIN --> T3
        MAIN --> T4
    end

    style MAIN fill:#4169E1,stroke:#000,stroke-width:3px,color:#fff
```

---

## Caching Strategy

```mermaid
graph TB
    subgraph "Redis Cache Layers"
        L1[L1: Device Status<br/>TTL: 5 minutes]
        L2[L2: Recent Telemetry<br/>TTL: 1 minute]
        L3[L3: Aggregated Data<br/>TTL: 15 minutes]
        L4[L4: API Key Validation<br/>TTL: 30 minutes]
    end

    subgraph "Cache Operations"
        READ[Read Request]
        WRITE[Write Request]
    end

    subgraph "PostgreSQL"
        PG[(Primary Database)]
    end

    READ --> L1
    L1 -->|Cache Miss| L2
    L2 -->|Cache Miss| L3
    L3 -->|Cache Miss| L4
    L4 -->|Cache Miss| PG
    
    WRITE --> PG
    PG -->|Update| L1
    PG -->|Invalidate| L2
    PG -->|Invalidate| L3

    style PG fill:#4169E1,stroke:#000,stroke-width:3px,color:#fff
    style L1 fill:#DC143C,stroke:#000,stroke-width:2px,color:#fff
    style L2 fill:#DC143C,stroke:#000,stroke-width:2px,color:#fff
    style L3 fill:#DC143C,stroke:#000,stroke-width:2px,color:#fff
    style L4 fill:#DC143C,stroke:#000,stroke-width:2px,color:#fff
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Compose Stack"
        subgraph "Application Tier"
            APP1[Flask App 1<br/>Gunicorn]
            APP2[Flask App 2<br/>Gunicorn]
            APP3[Flask App N<br/>Gunicorn]
        end

        subgraph "Message Broker"
            MQTT[Mosquitto MQTT<br/>Port 1883, 9001]
        end

        subgraph "Data Tier"
            PG[(PostgreSQL 15<br/>Port 5432)]
            REDIS[(Redis 7<br/>Port 6379)]
        end

        subgraph "Monitoring Tier"
            PROM[Prometheus<br/>Port 9090]
            GRAF[Grafana<br/>Port 3000]
            NODE[Node Exporter<br/>Port 9100]
        end

        subgraph "Volumes"
            V1[postgres_data]
            V2[redis_data]
            V3[prometheus_data]
            V4[grafana_data]
        end
    end

    APP1 --> PG
    APP2 --> PG
    APP3 --> PG

    APP1 --> REDIS
    APP2 --> REDIS
    APP3 --> REDIS

    APP1 --> MQTT
    APP2 --> MQTT
    APP3 --> MQTT

    APP1 --> PROM
    APP2 --> PROM
    APP3 --> PROM

    PROM --> GRAF
    NODE --> PROM

    PG --> V1
    REDIS --> V2
    PROM --> V3
    GRAF --> V4

    style PG fill:#4169E1,stroke:#000,stroke-width:3px,color:#fff
    style REDIS fill:#DC143C,stroke:#000,stroke-width:2px,color:#fff
    style MQTT fill:#FF6B6B,stroke:#000,stroke-width:2px
```

---

## Performance Optimization Strategy

```mermaid
graph TB
    subgraph "Query Optimization"
        Q1[Time-based Partitioning<br/>Reduce scan size]
        Q2[Composite Indexes<br/>device_id + timestamp]
        Q3[Materialized Views<br/>Pre-aggregated data]
        Q4[Query Result Caching<br/>Redis layer]
    end

    subgraph "Write Optimization"
        W1[Batch Inserts<br/>Bulk telemetry writes]
        W2[Async Processing<br/>Background workers]
        W3[Connection Pooling<br/>Reuse connections]
        W4[Write-Ahead Logging<br/>PostgreSQL WAL]
    end

    subgraph "Data Lifecycle"
        D1[Hot Data<br/>Last 7 days<br/>Full indexes]
        D2[Warm Data<br/>7-90 days<br/>Partial indexes]
        D3[Cold Data<br/>90+ days<br/>Compressed]
        D4[Archive<br/>1+ year<br/>External storage]
    end

    Q1 --> D1
    Q2 --> D1
    Q3 --> D2
    Q4 --> D1

    W1 --> D1
    W2 --> D1
    W3 --> D1
    W4 --> D1

    D1 -->|Age out| D2
    D2 -->|Age out| D3
    D3 -->|Age out| D4

    style D1 fill:#90EE90,stroke:#000,stroke-width:2px
    style D2 fill:#FFD700,stroke:#000,stroke-width:2px
    style D3 fill:#FFA500,stroke:#000,stroke-width:2px
    style D4 fill:#808080,stroke:#000,stroke-width:2px,color:#fff
```

---

## Migration Path from IoTDB to PostgreSQL

```mermaid
graph LR
    subgraph "Phase 1: Preparation"
        P1A[Create telemetry_data table]
        P1B[Set up partitioning]
        P1C[Create indexes]
    end

    subgraph "Phase 2: Dual Write"
        P2A[Write to both IoTDB & PostgreSQL]
        P2B[Validate data consistency]
        P2C[Monitor performance]
    end

    subgraph "Phase 3: Migration"
        P3A[Export historical data from IoTDB]
        P3B[Transform data format]
        P3C[Bulk import to PostgreSQL]
    end

    subgraph "Phase 4: Cutover"
        P4A[Switch reads to PostgreSQL]
        P4B[Stop IoTDB writes]
        P4C[Decommission IoTDB]
    end

    P1A --> P1B --> P1C
    P1C --> P2A --> P2B --> P2C
    P2C --> P3A --> P3B --> P3C
    P3C --> P4A --> P4B --> P4C

    style P4C fill:#90EE90,stroke:#000,stroke-width:3px
```

---

## Key Benefits of PostgreSQL for Telemetry

1. **Unified Database**: Single database for metadata and telemetry
2. **ACID Compliance**: Strong consistency guarantees
3. **Rich Query Language**: Full SQL support with CTEs, window functions
4. **JSON Support**: Native JSONB for flexible telemetry formats
5. **Mature Ecosystem**: Extensive tooling and monitoring
6. **Horizontal Scaling**: Citus extension for sharding
7. **Time-series Extensions**: TimescaleDB for optimized time-series
8. **Backup & Recovery**: Robust backup solutions (pg_dump, WAL archiving)

---

## Recommended PostgreSQL Extensions

```mermaid
graph TB
    PG[(PostgreSQL Core)]
    
    TS[TimescaleDB<br/>Time-series optimization]
    CITUS[Citus<br/>Horizontal scaling]
    POSTGIS[PostGIS<br/>Geospatial data]
    PGCRON[pg_cron<br/>Scheduled jobs]
    
    PG --> TS
    PG --> CITUS
    PG --> POSTGIS
    PG --> PGCRON
    
    TS --> OPT1[Automatic partitioning]
    TS --> OPT2[Compression]
    TS --> OPT3[Continuous aggregates]
    
    CITUS --> SCALE1[Distributed tables]
    CITUS --> SCALE2[Parallel queries]
    
    style PG fill:#4169E1,stroke:#000,stroke-width:3px,color:#fff
    style TS fill:#90EE90,stroke:#000,stroke-width:2px
    style CITUS fill:#FFD700,stroke:#000,stroke-width:2px
```

