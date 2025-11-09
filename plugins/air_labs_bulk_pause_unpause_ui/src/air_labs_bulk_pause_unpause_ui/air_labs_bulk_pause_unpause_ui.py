from __future__ import annotations
from pathlib import Path
from airflow.plugins_manager import AirflowPlugin
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

ui_app = FastAPI(title="Airflow BulkPauseUi")
STATIC_DIR = Path(__file__).resolve().parent / "static"
ui_app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

fastapi_ui = {
    "app": ui_app,
    "url_prefix": "/api/airflow_bulk_pause_unpause_ui",   # => /api/airflow-tools-ui/static/*
    "name": "AirflowBulkUnpausePauseUi",
}

class AirflowBulkUnpausePauseUi(AirflowPlugin):
    name = "plugins/airflow_bulk_pause_unpause_ui"
    fastapi_apps = [fastapi_ui]

    # LEFT NAV LINK
    external_views = [
        {
            "name": "Pause/Unpause",
            "href": "/api/airflow_bulk_pause_unpause_ui/static/index.html",  # our page
            "destination": "nav",      # shows under the main sidebar (works well)
            "url_route": "airflow_bulk_pause_unpause_ui"
        }
    ]

    # Remove/react_apps if you don’t want a dashboard widget
    react_apps = []