# 🧩 Bulk Pause / Unpause UI Plugin

The **Bulk Pause / Unpause UI** plugin provides a visual React-based interface inside Airflow for bulk pausing and unpausing DAGs.

---

## 🖥️ Overview

- React + Tailwind frontend embedded in the Airflow webserver  
- Interacts with the Bulk Pause API through `/api/airflow_bulk_pause_api/...`  
- Displays DAG list with filters and action buttons  
- Built using the Airflow Plugin AppBuilder integration

---

## 🎥 Demo

![Bulk Pause Demo](../../../demos/bulk_pause.gif)

---

## 🧮 Features

- Search and filter DAGs by name or tags  
- Bulk select and perform pause/unpause actions  
- Displays success and failure statuses inline  
- Responsive and styled using Tailwind CSS

---

## 🧱 Architecture

| Layer | Description |
|--------|--------------|
| React Frontend | Built using modern React (hooks + JSX) |
| FastAPI Backend | Handles REST communication via `AirflowClient` |
| Airflow Webserver | Hosts the static frontend under `/static/plugins/` |

---

## 🧾 License

MIT © [Rahul Rajasekharan](https://github.com/rahulrajasekharan)
