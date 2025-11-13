# 🚀 Air-Labs

> **Reusable, production-ready Apache Airflow plugins — powered by FastAPI + React.**

> A modular suite of UI and API extensions that make Airflow simpler, smarter, and more enjoyable to use.

> 🧩 This repository will continue to be updated with **reusable, open-source plugins** for Airflow — including APIs, UIs, and automation tools.


---
> ⚠️ **Note:**  
> The Air-Labs plugins are designed to **enhance developer experience** and **simplify data engineering workflows**.  
> The Air-Labs plugins uses the new React feature of Airflow 3.1 and hence it works only on Airflow >= 3.1
> While they are built with production-quality patterns, they **must be tested thoroughly** before use in production workloads to ensure stability and compatibility with your environment.

---

⭐ **If you like my work**, please **star the repo** and drop me a **like or comment on [LinkedIn](https://www.linkedin.com/in/rahul-rajasekharan-012506121/)** —  
or explore my **[portfolio](https://rahul-portfolio-roan-eight.vercel.app/)** to see more of what I build.  
Your encouragement motivates me to make this even better and release **more Airflow plugins in the coming weeks!**

## 🌟 Overview

**Air-Labs** enhances Apache Airflow by introducing modular plugins that extend its UI and API.  
Each plugin integrates seamlessly into the Airflow webserver — built using **FastAPI (backend)** and **React (frontend)** — and leverages Airflow’s stable REST API for automation.

> 🧩 This repository provides a growing collection of open-source, reusable Airflow extensions.

---

## 📦 Components Airflow

| Component | Description | Documentation |
|------------|--------------|----------------|
| **Helpers** | Core Python utilities and connection helpers used by all plugins. | [View Helpers Docs](plugins/air_labs_helpers/README.md) |
| **Bulk Pause / Unpause API** | FastAPI-based Airflow plugin to pause or unpause DAGs in bulk. | [View API Docs](plugins/air_labs_bulk_pause_api/README.md) |
| **Bulk Pause / Unpause UI** | React-powered UI extension integrated into the Airflow sidebar for bulk DAG control. | [View UI Docs](plugins/air_labs_bulk_pause_unpause_ui/README.md) |

## 📦 Components DBT
| Component | Description | Documentation |
|------------|--------------|----------------|
| **dbt-tools** | llm based docs cli tool for dbt. | [View Docs](dbt_tools/README.md) |

---

## 🎥 Demo

Bulk Pause / Unpause
👉 [Bulk Pause Demo](./demos/bulk_pause.gif)

---

## ⚙️ Installation

You can install the Air-Labs components directly from TestPyPI:

```bash
# Install helpers
pip install air-labs-helpers

# Install API plugin
pip install air-labs-bulk-pause-api

# Install UI plugin
pip install air-labs-bulk-pause-unpause-ui
```

---

## 🧠 Development

To work on the project locally:

```bash
uv venv --python 3.11 .venv
uv sync
```

---
## 🧾 License

MIT © [Rahul Rajasekharan](https://github.com/rahulrajasekharan)
