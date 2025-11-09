# 🧰 Airflow-Xtra Helpers

The **Helpers** module provides shared utilities used across all Airflow-Xtra plugins.  
It standardizes how plugins interact with the Airflow REST API and connection management.

---

## 🔧 Features

- Centralized API client (`AirflowClient`) for REST API interaction  
- Built-in authentication support using `/auth/token`  
- Simplified connection management via Airflow’s `conn_id`  
- Consistent response formatting and error handling

---

## 🧮 Usage Example

```python
from airflow_xtra_helpers.client import AirflowClient

client = AirflowClient(conn_id="airflow_api_conn")
report = client.pause_dags(name_prefix="etl_")
print(report)
```

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

### How It Works

1. Loads the Airflow connection from `conn_id`  
2. Authenticates via `/auth/token`  
3. Sends REST API requests to `/api/v1/...`  
4. Returns structured results

---

## 🧾 License

MIT © [Rahul Rajasekharan](https://github.com/rahulrajasekharan)
