from pathlib import Path
from ruamel.yaml import YAML
from typing import Dict, Any
import shutil
yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)


def _load_yaml(p: Path) -> dict:
    """
    Load a YAML file from disk if it exists.

    Reads and parses a YAML file into a Python dictionary using ``ruamel.yaml``.
    If the file does not exist or is empty, an empty dictionary is returned.

    Parameters
    ----------
    p : Path
        Path to the YAML file to load.

    Returns
    -------
    dict
        Parsed YAML content as a dictionary, or an empty dict if the file
        does not exist or is empty.

    Notes
    -----
    - This function preserves key and string quoting styles for round-trip editing.
    - Errors in YAML syntax will propagate as exceptions from ``ruamel.yaml``.
    """
    data = {}
    if p.exists():
        with p.open() as f:
            loaded = yaml.load(f)
            if loaded:
                data = loaded
    return data


def _dump_yaml(p: Path, data: dict):
    """
    Write a Python dictionary to disk as YAML.

    Ensures the parent directory exists, then serializes the given data
    structure to the specified path using ``ruamel.yaml``.

    Parameters
    ----------
    p : Path
        Destination path for the YAML file.
    data : dict
        Dictionary to be written as YAML.

    Notes
    -----
    - Indentation and quote preservation are controlled globally in this module.
    - Overwrites any existing file content.
    """
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        yaml.dump(data, f)


def _find_or_create_model_entry(schema: dict, model_name: str) -> Dict[str, Any]:
    """
    Locate or create a model entry in a dbt schema.yml dictionary.

    Searches the ``models`` list for an entry with the specified model name.
    If not found, creates a new model entry and appends it to the list.

    Parameters
    ----------
    schema : dict
        Parsed YAML structure from a schema.yml file.
    model_name : str
        The name of the dbt model to locate or create.

    Returns
    -------
    Dict[str, Any]
        The model dictionary within the schema structure.

    Notes
    -----
    This helper ensures that the schema always has the form:
    ```
    models:
      - name: <model_name>
        columns: [...]
    ```
    """
    models = schema.setdefault("models", [])
    for m in models:
        if isinstance(m, dict) and m.get("name") == model_name:
            return m
    new_m = {"name": model_name}
    models.append(new_m)
    return new_m

def write_schema_descriptions(
    schema_path: Path,
    model_name: str,
    model_desc: str | None,
    column_descs: dict[str, str],
    overwrite: bool = True,
):
    """
    Safely update or create model and column descriptions in a dbt schema.yml file.

    This version is **non-destructive** — it preserves any existing tests, meta fields,
    or other custom YAML keys. It only modifies or adds description fields.

    Parameters
    ----------
    schema_path : Path
        Path to the schema.yml file to read and update.
    model_name : str
        Name of the dbt model to update or insert.
    model_desc : str | None
        New description for the model. If None, model description is left unchanged.
    column_descs : dict[str, str]
        Mapping of column names to generated descriptions.
    overwrite : bool, optional
        Whether to overwrite existing descriptions if they already exist.
        Defaults to False.

    Behavior
    --------
    - If the file does not exist, it is created.
    - If the model entry does not exist, it is appended to the models list.
    - Each column entry is merged in-place.
    - Existing fields (tests, meta, tags, etc.) are preserved.

    Example
    -------
    >>> write_schema_descriptions(
    ...     Path("models/schema.yml"),
    ...     "stg_orders",
    ...     "Staging model for order data.",
    ...     {"order_id": "Unique order identifier."},
    ...     overwrite=False
    ... )
    """
    # Load schema
    schema = _load_yaml(schema_path)

    # Create a backup before first write (safety measure)
    backup_path = schema_path.with_suffix(".bak.yml")
    if schema_path.exists() and not backup_path.exists():
        shutil.copy(schema_path, backup_path)

    # Find or create model entry
    model_entry = _find_or_create_model_entry(schema, model_name)

    # Update model-level description
    if model_desc:
        if overwrite or not (model_entry.get("description") or "").strip():
            model_entry["description"] = model_desc.strip()

    # Merge column descriptions safely
    cols = model_entry.setdefault("columns", [])
    by_name = {c.get("name"): c for c in cols if isinstance(c, dict) and "name" in c}

    for col_name, desc in (column_descs or {}).items():
        if not desc:
            continue
        existing = by_name.get(col_name, {"name": col_name})
        # Preserve all existing metadata, only update description if needed
        if overwrite or not (existing.get("description") or "").strip():
            existing["description"] = desc.strip()
        by_name[col_name] = existing

    # Preserve original order as much as possible
    updated_cols = []
    seen = set()
    for c in cols:
        name = c.get("name")
        if name in by_name:
            updated_cols.append(by_name[name])
            seen.add(name)
    # Add any new columns that weren’t present
    for name, c in by_name.items():
        if name not in seen:
            updated_cols.append(c)

    model_entry["columns"] = updated_cols

    # Write updated YAML
    _dump_yaml(schema_path, schema)