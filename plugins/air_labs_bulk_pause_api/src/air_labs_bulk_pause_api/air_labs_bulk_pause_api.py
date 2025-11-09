from __future__ import annotations
import os
from typing import Optional, List

from airflow.plugins_manager import AirflowPlugin
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Import the reusable Airflow REST API client
from air_labs_helpers.air_labs_plugins_helper import AirflowClient


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------
def get_client() -> AirflowClient:
    """
    Return a ready-to-use AirflowClient instance.

    Notes
    -----
    The client automatically uses session-based authentication when running inside
    the Airflow webserver (no password required). When called from inside a plugin,
    it can access `/api/v2/...` endpoints directly.

    Returns
    -------
    AirflowClient
        A new client instance connected to the local Airflow webserver.
    """
    return AirflowClient()  # session auth will be used implicitly


# ---------------------------------------------------------------------------
# FastAPI Application Definition
# ---------------------------------------------------------------------------

# Create the FastAPI application that will serve our endpoints
app = FastAPI(title="Airflow Bulk Pause API")

# Read trusted hosts from environment, defaulting to '*' (all hosts)
_raw = os.getenv("HELLO_ALLOWED_HOSTS", "*")
allowed = [h.strip() for h in _raw.split(",") if h.strip()] or ["*"]

# Middleware to restrict requests to trusted hosts (basic security)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed)


def normalize_tags(tags: Optional[str]) -> List[str]:
    """
    Convert a comma-separated string of tags into a list.

    Parameters
    ----------
    tags : Optional[str]
        Comma-separated list of tag names (e.g., "finance,etl,nightly").

    Returns
    -------
    List[str]
        A list of clean tag names. Empty if `tags` is None or blank.
    """
    if not tags:
        return []
    return [t.strip() for t in tags.split(",") if t.strip()]


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/pause_dags/")
def pause_dags(name_prefix: Optional[str] = "", tags: Optional[str] = ""):
    """
    Pause all DAGs that match a given prefix and/or set of tags.

    Query Parameters
    ----------------
    name_prefix : str, optional
        Only pause DAGs whose IDs start with this prefix.
        Leave empty to apply to all DAGs.
    tags : str, optional
        Comma-separated list of tags (e.g., "etl,nightly").
        Only DAGs containing *all* of these tags will be paused.

    Returns
    -------
    dict
        Example response:
        {
            "ok": true,
            "action": "pause",
            "tags": ["etl", "nightly"],
            "result": [
                {"dag_id": "dag_a", "changed": true, "message": "Updated"},
                {"dag_id": "dag_b", "changed": false, "message": "No-op"}
            ]
        }
    """
    tags_list = normalize_tags(tags)
    client = get_client()

    # Perform the API operation via AirflowClient
    all_results = client.pause_dags(name_prefix=name_prefix, tag_match="all", tags=tags_list)

    # Keep only entries that actually changed state (for cleaner responses)
    changed = [r for r in all_results if r.get("changed")]

    return {"ok": True, "action": "pause", "tags": tags_list, "result": changed}


@app.get("/unpause_dags/")
def unpause_dags(name_prefix: Optional[str] = "", tags: Optional[str] = ""):
    """
    Unpause all DAGs that match a given prefix and/or set of tags.

    Query Parameters
    ----------------
    name_prefix : str, optional
        Only unpause DAGs whose IDs start with this prefix.
        Leave empty to apply to all DAGs.
    tags : str, optional
        Comma-separated list of tags (e.g., "finance,core").
        Only DAGs containing *all* of these tags will be unpaused.

    Returns
    -------
    dict
        Example response:
        {
            "ok": true,
            "action": "unpause",
            "tags": ["finance"],
            "result": [
                {"dag_id": "dag_sales_report", "changed": true, "message": "Updated"}
            ]
        }
    """
    tags_list = normalize_tags(tags)
    client = get_client()

    all_results = client.unpause_dags(name_prefix=name_prefix, tag_match="all", tags=tags_list)
    changed = [r for r in all_results if r.get("changed")]

    return {"ok": True, "action": "unpause", "tags": tags_list, "result": changed}


# ---------------------------------------------------------------------------
# Plugin Registration
# ---------------------------------------------------------------------------

# Metadata object defining how Airflow should mount this FastAPI app
fastapi_app_with_metadata = {
    "app": app,
    "url_prefix": "/api/airflow-bulk-pause-api",  # Base path under which the app is exposed
    "name": "Airflow Tools API",
}


class AirflowBulkPause(AirflowPlugin):
    """
    Airflow Plugin definition that registers the FastAPI app.

    This makes the plugin discoverable by Airflow's plugin manager, so the
    API becomes available under `/api/airflow-tools-api`.

    Attributes
    ----------
    name : str
        Unique name used by Airflow to identify this plugin.
    fastapi_apps : list
        A list of FastAPI app configurations to be mounted.
    """
    name = "airflow_bulk_pause_api"
    fastapi_apps = [fastapi_app_with_metadata]


