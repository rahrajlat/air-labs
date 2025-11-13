# 🧩 Bulk Pause / Unpause API Plugin

The **Bulk Pause / Unpause API** provides REST endpoints to manage DAGs programmatically — enabling bulk control over DAGs using prefix or tag-based filters.

---

## ⚙️ Overview

- Built using **FastAPI**  
- Communicates with Airflow’s **core REST API**  
- Provides endpoints to pause, unpause, or list DAGs  
- Integrated authentication via Airflow’s `/auth/token`

---

## 🔧 Features

- Centralized API client (`AirflowClient`) for REST API interaction  
- Built-in authentication support using `/auth/token`  
- Simplified connection management via Airflow’s `conn_id`  
- Consistent response formatting and error handling

---

## 📦 Installation

```bash
pip install air-labs-bulk-pause-api
```

---
## 🎥 Demo

Bulk Pause / Unpause  
👉 **[View Demo](../../demos/bulk_pause.gif)**

### Connection Setup (Required)

Before using the client, **create a connection** in the Airflow UI → *Admin → Connections*.

| Field | Description | Example |
|--------|--------------|----------|
| Conn Id | Used in code | `airflow_api_conn` |
| Conn Type | `http` or `https` | `http` |
| Host | Airflow Webserver | `http://localhost:8080` |
| Login | Username / Service Account | `admin` |
| Password | Password or API token | `mysecret` |

---


## 🧱 High-Level Architecture

```mermaid
flowchart TD
    U[User or Script] --> X[Airflow Xtra API]
    subgraph Airflow Webserver
      X --> A[Auth Token Endpoint]
      X --> R[Airflow REST API v2]
    end
    R --> S[Scheduler or Executor]
    S --> D[DAGs and Tasks]

    subgraph Airflow Connection
      C1[Conn Type http or https]
      C2[Host webserver]
      C3[Port optional]
      C4[Login Password]
      C5[Conn id airflow_api_conn]
    end
    X -. uses .-> C1
    X -. uses .-> C2
    X -. uses .-> C3
    X -. uses .-> C4
    X -. uses .-> C5
```


## 🧩 Component View

```mermaid
flowchart LR
    subgraph Plugin
      H[Helpers AirflowClient<br/>resolve conn id<br/>token auth<br/>REST calls]
      F[FastAPI Routes<br/>pause unpause list]
    end

    UI[React UI optional] --> F
    S[Scripts or CLI] --> F

    F --> H
    H --> AR[Airflow REST API v2]
    H --> AT[Auth Token Endpoint]

    AR --> SCH[Scheduler or Executor]
    SCH --> DAG[DAGs and Tasks]
```

## 🧩 Example Endpoints

| Endpoint | Method | Description |
|-----------|---------|--------------|
| `/api/airflow_bulk_pause_api/pause` | POST | Pause matching DAGs |
| `/api/airflow_bulk_pause_api/unpause` | POST | Unpause matching DAGs |
| `/api/airflow_bulk_pause_api/list` | GET | List all active DAGs |

---

## 🧪 Example Usage

```bash
curl -X POST http://localhost:8080/api/airflow_bulk_pause_api/pause -d '{"name_prefix": "etl_"}'
```

Response:

```json
{
  "paused": ["etl_orders", "etl_customers"],
  "skipped": ["daily_cleanup"]
}
```

---

## 🧱 Architecture

- FastAPI routes registered through the Airflow plugin manager  
- Uses `AirflowClient` (from helpers) for backend communication  
- Returns structured JSON responses for UI or automation scripts

---

## 🧾 License

MIT © [Rahul Rajasekharan](https://github.com/rahulrajasekharan)
