# 🚀 Air-Labs

**A curated collection of reusable, production-friendly tools for Apache Airflow and dbt.**

Air-Labs focuses on **developer experience** and **workflow acceleration** for data engineers:
- React-based UI plugins for Airflow
- FastAPI-powered API extensions
- LLM-assisted tooling for dbt (with more dbt utilities coming soon)

This repository acts as a **hub/index** – each component has its own dedicated README with details, setup steps, and examples.

---

## 🧩 What’s Included

### 1. Airflow Plugins

Air-Labs plugins are built for **Airflow ≥ 3.1**, using the new React-based plugin framework.  
They integrate directly into the Airflow web UI and/or webserver process.

| Plugin | Type | Summary | Docs |
|--------|------|---------|------|
| **Air-Labs Helpers** | Core library | Shared Python helpers for all plugins (connections, logging, request helpers, etc.). | [`plugins/air_labs_helpers/README.md`](plugins/air_labs_helpers/README.md) |
| **Bulk Pause / Unpause API** | FastAPI plugin | Adds a REST API to pause/unpause multiple DAGs in a single call. Great for maintenance windows and bulk operations. | [`plugins/air_labs_bulk_pause_api/README.md`](plugins/air_labs_bulk_pause_api/README.md) |
| **Bulk Pause / Unpause UI** | React UI | Airflow sidebar UI to search, filter, and pause/unpause DAGs in bulk directly from the browser. | [`plugins/air_labs_bulk_pause_unpause_ui/README.md`](plugins/air_labs_bulk_pause_unpause_ui/README.md) |

> 🔎 See each plugin’s README for:
> - Installation & deployment
> - Screenshots / GIF demos
> - Configuration & API details

---

### 2. dbt Tools (Sub-Category)

Air-Labs also includes a growing set of **dbt-focused utilities** aimed at improving documentation, discoverability, and metadata quality.

| Tool | Focus | Summary | Docs |
|------|-------|---------|------|
| **dbt-power-tools** | LLM-powered docs | CLI to auto-generate dbt model & column descriptions using LLMs (Ollama-first), with optional SQL-aware logic and data profiling via `profiles.yml`. | [`dbt_tools/README.md`](dbt_tools/README.md) |

> 🧱 More dbt tools will be added over time (lineage helpers, test explorers, catalog views, etc.). This README will remain the **index** to those tools.

---

## ⚠️ Compatibility Overview

- **Airflow plugins**  
  - Designed for **Apache Airflow 3.1+**  
  - Rely on the new React UI plugin framework  
  - Should be tested thoroughly in your specific deployment (executor, auth, etc.)

- **dbt tools**  
  - Expect a compiled dbt project with `manifest.json` (and ideally `catalog.json`) under `target/`  
  - Some features (like profiling) read from `profiles.yml` to connect to your warehouse  
  - Work alongside, not instead of, the normal dbt CLI

---

## 🧭 How to Navigate This Repo

Use this root README as the **landing page**. For details, go to:

- Airflow helpers: `plugins/air_labs_helpers/README.md`
- Bulk Pause/Unpause API: `plugins/air_labs_bulk_pause_api/README.md`
- Bulk Pause/Unpause UI: `plugins/air_labs_bulk_pause_unpause_ui/README.md`
- dbt tools (LLM docs): `dbt_tools/README.md`

Each subcomponent’s README covers:
- Exact installation steps
- Configuration examples
- Code snippets
- Demo GIFs

---

## 🙌 Support & Contact

If you find this useful, you can:

- ⭐ Star the repository  
- 🔗 Connect on LinkedIn: https://www.linkedin.com/in/rahul-rajasekharan-012506121/  
- 🌐 Explore more projects: https://rahul-portfolio-roan-eight.vercel.app/

Feedback, issue reports, and ideas for new plugins/tools are always welcome 🚀

---

## 🧾 License

MIT © Rahul Rajasekharan
