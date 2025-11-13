import json
from pathlib import Path
from typing import Dict, Any, Iterable, List


def load_catalog(target_dir: str | Path) -> Dict[str, Any] | None:
    p = Path(target_dir) / "catalog.json"
    if not p.exists():
        return None
    with p.open() as f:
        return json.load(f)

import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml  # PyYAML


import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml  # PyYAML


def load_profiles_yml(path: str | Path | None = None) -> Optional[Dict[str, Any]]:
    """
    Load a dbt ``profiles.yml`` file and return its contents as a dictionary.

    dbt uses ``profiles.yml`` to store connection profiles, including credentials
    and target configurations for warehouses such as Postgres, Redshift, Snowflake,
    BigQuery, and others.

    This helper reads and parses that file so the calling code can extract
    adapter-specific connection settings for use in downstream clients.

    Parameters
    ----------
    path : str | Path | None, optional
        - If None, defaults to ``~/.dbt/profiles.yml``.
        - If a directory, looks for ``profiles.yml`` inside that directory.
        - If a file path, uses it as-is.

    Returns
    -------
    Dict[str, Any] | None
        Dictionary representation of the ``profiles.yml`` contents,
        or ``None`` if the file does not exist.

    Raises
    ------
    RuntimeError
        If the file exists but cannot be parsed as valid YAML.
    """
    if path is None:
        # Default: ~/.dbt/profiles.yml
        p = Path(os.path.expanduser("~")) / ".dbt" / "profiles.yml"
    else:
        p = Path(path)
        # If caller passed a directory (e.g. "."), append profiles.yml
        if p.is_dir():
            p = p / "profiles.yml"

    if not p.exists():
        return None

    try:
        with p.open() as f:
            data = yaml.safe_load(f)
            return data or {}
    except yaml.YAMLError as e:
        raise RuntimeError(f"Failed to parse profiles.yml at {p}: {e}") from e

def columns_from_catalog(node: Dict[str, Any], catalog: Dict[str, Any] | None) -> dict[str, dict]:
    """
    Return {column_name: {"data_type": <type>}} for this node using catalog.json.
    """
    if not catalog:
        return {}
    uid = node.get("unique_id")
    cnode = (catalog.get("nodes") or {}).get(uid)
    if not cnode:
        return {}
    out: dict[str, dict] = {}
    for name, meta in (cnode.get("columns") or {}).items():
        out[name] = {"data_type": meta.get("type")}
    return out

def load_manifest(target_dir: str | Path) -> Dict[str, Any]:
    """
    Load a dbt manifest file from the specified target directory.

    This function locates and parses the ``manifest.json`` file produced by
    ``dbt docs generate``.  The manifest contains metadata about all dbt
    resources—models, seeds, sources, macros, tests, etc.—and is required
    for discovering models to document.

    Parameters
    ----------
    target_dir : str | Path
        Path to the dbt target directory that contains ``manifest.json``.
        This can be a string or a Path object.

    Returns
    -------
    Dict[str, Any]
        The parsed manifest contents as a Python dictionary.

    Raises
    ------
    FileNotFoundError
        If ``manifest.json`` does not exist under the given ``target_dir``.
    JSONDecodeError
        If the file cannot be parsed as valid JSON.
    """
    p = Path(target_dir) / "manifest.json"
    if not p.exists():
        raise FileNotFoundError(
            f"manifest.json not found at {p}. Run `dbt docs generate` or check --target-dir."
        )
    with p.open() as f:
        return json.load(f)


def list_model_nodes(manifest: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """
    Extract model nodes from a dbt manifest dictionary.

    Iterates through the ``nodes`` section of the manifest and returns only
    entries whose ``resource_type`` is ``"model"``.  This effectively filters
    out tests, seeds, macros, and other resource types.

    Parameters
    ----------
    manifest : Dict[str, Any]
        The full manifest dictionary loaded from ``manifest.json``.

    Returns
    -------
    Iterable[Dict[str, Any]]
        A list (or other iterable) of model node dictionaries, each describing
        a single dbt model and its metadata such as name, path, columns, and tags.

    Notes
    -----
    - Disabled models are not filtered here; callers may apply additional
      filtering if required.
    - The manifest schema may differ slightly across dbt versions, so missing
      keys should be handled defensively by the caller.
    """
    nodes: List[Dict[str, Any]] = []
    for node in manifest.get("nodes", {}).values():
        if node.get("resource_type") == "model":
            nodes.append(node)
    return nodes