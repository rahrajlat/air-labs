from pathlib import Path
from typing import Any

def coerce_path(p: Any) -> Path:
    # Accept Path, str, or Typer's OptionInfo (use its .default)
    if isinstance(p, Path):
        return p
    if isinstance(p, str):
        return Path(p)
    default = getattr(p, "default", None)
    if isinstance(default, (str, Path)):
        return Path(default)
    raise TypeError(f"Expected str|Path, got {type(p).__name__}")

def format_column_stats_md(col_profile: dict) -> str:
    """
    Format a single column's profile dict as a Markdown table.
    Suitable for embedding in dbt column descriptions.
    """
    if not col_profile:
        return ""

    missing_pct = col_profile.get("missing_pct")
    unique_pct = col_profile.get("unique_pct")

    def fmt(val, digits=2):
        if val is None:
            return "n/a"
        if isinstance(val, float):
            return f"{val:.{digits}f}"
        return str(val)

    example_values = col_profile.get("example_values") or []
    examples_str = ", ".join(str(v) for v in example_values[:5]) if example_values else "n/a"

    missing_str = f"{missing_pct * 100:.1f}%" if missing_pct is not None else "n/a"
    unique_str = f"{unique_pct * 100:.1f}%" if unique_pct is not None else "n/a"

    lines = [
        "",
        "**Column statistics**",
        "",
        "| Metric       | Value                |",
        "|-------------|----------------------|",
        f"| Missing %    | {missing_str}       |",
        f"| Unique %     | {unique_str}        |",
        f"| Min          | {fmt(col_profile.get('min'))} |",
        f"| Max          | {fmt(col_profile.get('max'))} |",
        f"| Mean         | {fmt(col_profile.get('mean'))} |",
        f"| Std dev      | {fmt(col_profile.get('std'))} |",
        f"| Examples     | {examples_str}      |",
    ]

    return "\n".join(lines)

def pick_column_profile(profile_summary: dict | None, column_name: str) -> dict | None:
    """
    Return the profiling information for a specific column from the full
    profile summary produced by `profile_query_for_llm`.

    Parameters
    ----------
    profile_summary : dict | None
        The full profile dict, containing keys like "row_count",
        "n_columns", "columns": [ ... ].
    column_name : str
        The name of the column whose profile is requested.

    Returns
    -------
    dict | None
        The column's profile dictionary, or None if the column is not found
        or profile_summary is None.
    """
    if not profile_summary:
        return None

    columns = profile_summary.get("columns", [])
    for col in columns:
        if col.get("name") == column_name:
            return col

    return None