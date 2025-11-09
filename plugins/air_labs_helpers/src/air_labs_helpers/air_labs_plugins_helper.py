import time
import requests
from typing import Iterable, Optional, Literal, Dict, Any, List

from airflow.hooks.base import BaseHook  # Airflow 2/3
import urllib

class AirflowAPIError(RuntimeError):
    pass


class AirflowClient:
    """
    Airflow REST API client that *only* pulls config & credentials from an Airflow Connection.

    Usage:
        client = AirflowClient(conn_id="airflow_api_conn")
        report = client.pause_dags(name_prefix="etl_")

    Connection requirements:
      - Conn Type: http or https
      - Host: webserver host (optionally with scheme)
      - Port: optional
      - Login/Password: service account for /auth/token
    """

    def __init__(
        self,
        conn_id: str = "airflow_api_conn",
        *,
        timeout: int = 30,
        page_size: int = 100,
        max_retries: int = 3,
        backoff: float = 0.8,
    ):
        self.conn_id = conn_id
        self.timeout = timeout
        self.page_size = page_size
        self.max_retries = max_retries
        self.backoff = backoff

        self._session = requests.Session()
        self._token: Optional[str] = None
        self._token_exp: float = 0.0  # unix seconds

        # populated by _load_from_connection()
        self._base = ""
        self._user: Optional[str] = None
        self._pass: Optional[str] = None

        self._load_from_connection()

    # ---------- connection & auth ----------
    def _load_from_connection(self) -> None:
        conn = BaseHook.get_connection(self.conn_id)

        extra = (conn.extra_dejson or {}) if hasattr(conn, "extra_dejson") else {}
        base_url = (extra.get("base_url") or "").strip()

        if not base_url:
            schema = (conn.schema or conn.conn_type or "http").strip()
            host = (conn.host or "").strip()
            if host.startswith(("http://", "https://")):
                base_url = host
            else:
                if not host:
                    raise ValueError(
                        f"Connection '{self.conn_id}' missing host and extra.base_url"
                    )
                port = f":{conn.port}" if conn.port else ""
                base_url = f"{schema}://{host}{port}"

        self._base = base_url.rstrip("/")
        self._user = conn.login
        self._pass = conn.password

        if not (self._user and self._pass):
            raise ValueError(
                f"Connection '{self.conn_id}' must provide login/password for /auth/token"
            )

        # nuke token so we’ll mint a new one under the new creds
        self._token = None
        self._token_exp = 0.0

    def _ensure_token(self) -> str:
        now = time.time()
        if self._token and now < (self._token_exp - 60):
            return self._token

        # Re-load in case the Connection rotated in the backend
        self._load_from_connection()

        resp = self._session.post(
            f"{self._base}/auth/token",
            json={"username": self._user, "password": self._pass},
            timeout=self.timeout,
        )
        if resp.status_code >= 500:
            raise AirflowAPIError(f"Server error {resp.status_code}: {resp.text}")
        resp.raise_for_status()

        data = resp.json()
        token = data.get("access_token")
        if not token:
            raise RuntimeError("Auth succeeded but no access_token returned.")

        self._token = token
        ttl = int(data.get("expires_in", 900))
        self._token_exp = now + ttl
        return token

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._ensure_token()}",
            "Content-Type": "application/json",
        }

    # single place to perform authenticated requests; retries 5xx + refreshes on 401 once
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self._base}{endpoint}"
        # first attempt with current/ensured token
        attempt = 0
        while True:
            try:
                headers = kwargs.pop("headers", {})
                headers.update(self._headers())
                resp = self._session.request(
                    method.upper(), url, timeout=self.timeout, headers=headers, **kwargs
                )
                if resp.status_code == 401:
                    # clear token and try once more
                    if attempt == 0:
                        self._token = None
                        self._token_exp = 0.0
                        attempt += 1
                        continue
                if resp.status_code >= 500:
                    raise AirflowAPIError(f"Server error {resp.status_code}: {resp.text}")
                return resp
            except (requests.ConnectionError, requests.Timeout, AirflowAPIError):
                attempt += 1
                if attempt > self.max_retries:
                    raise
                time.sleep(self.backoff * (2 ** (attempt - 1)))

    # ---------- generic requests ----------
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        resp = self._request("GET", endpoint, params=params or {})
        resp.raise_for_status()
        return resp.json()

    def patch(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = self._request("PATCH", endpoint, json=payload)
        resp.raise_for_status()
        return resp.json()

    # ---------- helpers ----------
    @staticmethod
    def _tags_from_dag(d: Dict[str, Any]) -> set[str]:
        tags = d.get("tags") or []
        out: set[str] = set()
        for t in tags:
            if isinstance(t, dict) and "name" in t:
                out.add(str(t["name"]))
            elif isinstance(t, str):
                out.add(t)
        return out

    # ---------- high-level API ----------
    def list_dags(self) -> List[Dict[str, Any]]:
        """Return ALL DAGs (auto-paginates)."""
        items: List[Dict[str, Any]] = []
        offset = 0
        while True:
            data = self.get("/api/v2/dags", params={"limit": self.page_size, "offset": offset})
            batch = data.get("dags", [])
            if not batch:
                break
            items.extend(batch)
            total = data.get("total_entries")
            if total is not None and len(items) >= total:
                break
            offset += len(batch)
        return items

    def set_pause_state_for_dags(
        self,
        *,
        action: Literal["pause", "unpause"],
        name_prefix: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        tag_match: Literal["any", "all"] = "any",
        dry_run: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Pause or unpause DAGs filtered by name prefix and/or tags.
        Returns per-DAG report dicts.
        """
        target_paused = (action == "pause")
        tag_set = set(tags or [])
        report: List[Dict[str, Any]] = []

        for dag in self.list_dags():
            dag_id = dag.get("dag_id", "")
            is_paused = bool(dag.get("is_paused", False))
            dag_tags = self._tags_from_dag(dag)

            # name filter
            if name_prefix and not dag_id.startswith(name_prefix):
                report.append({
                    "dag_id": dag_id, "matched": False, "was_paused": is_paused,
                    "target_paused": target_paused, "changed": False,
                    "status_code": None, "message": "Skipped (prefix mismatch)"
                })
                continue

            # tag filter
            matched = True
            if tag_set:
                matched = tag_set.issubset(dag_tags) if tag_match == "all" else bool(tag_set & dag_tags)
            if not matched:
                report.append({
                    "dag_id": dag_id, "matched": False, "was_paused": is_paused,
                    "target_paused": target_paused, "changed": False,
                    "status_code": None,
                    "message": f"Skipped (tags mismatch: have {sorted(dag_tags)})"
                })
                continue

            # no-op
            if is_paused == target_paused:
                report.append({
                    "dag_id": dag_id, "matched": True, "was_paused": is_paused,
                    "target_paused": target_paused, "changed": False,
                    "status_code": 200, "message": "No-op (already in target state)"
                })
                continue

            if dry_run:
                report.append({
                    "dag_id": dag_id, "matched": True, "was_paused": is_paused,
                    "target_paused": target_paused, "changed": False,
                    "status_code": None, "message": f"Would PATCH is_paused={target_paused}"
                })
                continue

            # apply change
            try:
                resp = self.patch(f"/api/v2/dags/{dag_id}", {"is_paused": target_paused})
                report.append({
                    "dag_id": dag_id, "matched": True, "was_paused": is_paused,
                    "target_paused": target_paused, "changed": True,
                    "status_code": 200, "message": "Updated", "response": resp
                })
            except requests.HTTPError as e:
                status = e.response.status_code if e.response is not None else None
                report.append({
                    "dag_id": dag_id, "matched": True, "was_paused": is_paused,
                    "target_paused": target_paused, "changed": False,
                    "status_code": status, "message": f"ERROR: {e}"
                })
        return report
    
    

    def _seg(self,s: str) -> str:
        return urllib.parse.quote(str(s), safe="")  # encode +, :, etc.

    def fail_task(
        self,
        dag_id: str,
        dag_run_id: str,
        task_id: str,
        *,
        map_index: int = -1,
    ) -> Dict[str, Any]:
        """
        Force a task instance into 'failed' state in Airflow 3.1.
        PATCH /api/v1/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}[/{map_index}]?update_mask=state
        Body: {"state": "failed"}
        """
        endpoint = (
            f"/api/v2/dags/{self._seg(dag_id)}/dagRuns/{self._seg(dag_run_id)}/taskInstances/{self._seg(task_id)}"
        )
        if map_index is not None and map_index >= 0:
            endpoint += f"/{map_index}"
        resp = self._request("PATCH", endpoint, json={"new_state": "failed"})
        resp.raise_for_status()
        return resp.json()

    # convenience wrappers
    def pause_dags(self, **kwargs) -> List[Dict[str, Any]]:
        return self.set_pause_state_for_dags(action="pause", **kwargs)

    def unpause_dags(self, **kwargs) -> List[Dict[str, Any]]:
        return self.set_pause_state_for_dags(action="unpause", **kwargs)