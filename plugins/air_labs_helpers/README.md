# 🧰 Air-Labs Helpers

The **Air-Labs Helpers** module provides the shared utilities that power all Air-Labs plugins.  
It standardizes how plugins authenticate, communicate with the Airflow REST API, and manage connections — ensuring consistency across both API and UI extensions.

---

## 🔧 Features

- 🚀 **Unified API Client** (`AirflowClient`) for interacting with the Airflow REST API  
- 🔐 **Automatic authentication** using Airflow’s `/auth/token` endpoint  
- 🔌 **Connection-based configuration** via Airflow’s `conn_id`  
- 🧹 **Consistent error handling and response formatting**  
- 🧱 Foundation used by all other Air-Labs plugin packages

---

## 📦 Installation

```bash
pip install air-labs-helpers
```

---

## 🧮 Example Usage

```python
from air_labs_helpers.client import AirflowClient

client = AirflowClient(conn_id="airflow_api_conn")
report = client.pause_dags(name_prefix="etl_")
print(report)
```

---

## 🔌 Connection Setup (Required)

Before using the client, create a connection in:

**Airflow UI → Admin → Connections**

| Field | Description | Example |
|--------|-------------|-----------|
| Conn Id | Used by your code | `airflow_api_conn` |
| Conn Type | Must be `http` or `https` | `http` |
| Host | Airflow Webserver URL | `http://localhost:8080` |
| Login | Username or service account | `admin` |
| Password | Password or API token | `mysecret` |

---

## ⚙️ How It Works

1. Loads connection details using the provided `conn_id`  
2. Authenticates with Airflow via `/auth/token`  
3. Calls the appropriate `/api/v1/...` endpoints  
4. Returns structured JSON responses for easy consumption

---

## 🎥 Demo

Bulk Pause / Unpause  
👉 **[View Demo](../../demos/bulk_pause.gif)**

---

## 🧾 License

MIT © [Rahul Rajasekharan](https://github.com/rahulrajasekharan)
