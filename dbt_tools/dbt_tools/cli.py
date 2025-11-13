"""
dbt-llm-docs CLI Tool
=====================

This module implements a Typer-based command-line interface that uses
a local or remote large language model (LLM) to generate documentation
for dbt models and columns. The generated text is written into the
project's ``schema.yml`` files so it can appear in `dbt docs serve`.

Commands
--------
- ``init``:  Bootstrap default Jinja2 prompt templates under <project>/prompts.
- ``list``:  Display available dbt models using selection, exclusion, and tag filters.
- ``generate``:  Generate model and column documentation via an LLM (currently Ollama).

The tool reads ``target/manifest.json`` produced by ``dbt docs generate``
to discover models and columns.
"""

import sys
import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from rich.spinner import Spinner
from rich.live import Live
from .dbt_io.loader import load_manifest, list_model_nodes,load_catalog,columns_from_catalog,load_profiles_yml
from .dbt_io.selector import select_models
from .dbt_io.writer import write_schema_descriptions
from .backends.ollama_backend import OllamaBackend
from .backends.openai_backend import OpenAIBackend
from .util import coerce_path,pick_column_profile,format_column_stats_md
from .database_connectors import database_connector

app = typer.Typer(add_completion=False)
console = Console()


def _env(project_dir: Path) -> Environment:
    """
    Build a Jinja2 Environment for loading prompt templates.

    Prompt templates are searched first in the project's ``prompts`` folder
    (``<project_dir>/prompts``), then in the package's built-in fallback path
    ``dbt_llm_docs/prompts``.

    Parameters
    ----------
    project_dir : Path
        Path to the dbt project directory (may be relative such as ".").

    Returns
    -------
    Environment
        Configured Jinja2 Environment whose loader searches both prompt locations.
    """
    project_dir = coerce_path(project_dir).resolve()
    search_paths = [
        project_dir / "prompts",
        Path(__file__).parent / "prompts",
    ]
    str_paths = [str(p) for p in search_paths if p.exists()]
    if not str_paths:
        str_paths = [str(Path(__file__).parent / "prompts")]
    return Environment(loader=FileSystemLoader(str_paths))


@app.command()
def init(project_dir: Path = typer.Option(".", help="dbt project dir")):
    """
    Initialize default Jinja2 prompt templates inside ``<project_dir>/prompts``.

    Creates two templates if they do not already exist:

    - ``model.md.j2`` — prompt used to describe dbt models.
    - ``column.md.j2`` — prompt used to describe dbt model columns.

    Parameters
    ----------
    project_dir : Path, optional
        Path to the dbt project directory (default: current working directory).
    """
    target = project_dir / "prompts"
    target.mkdir(parents=True, exist_ok=True)
    defaults = {
        "model.md.j2": """You are documenting a dbt model for data analysts.
Model name: {{ model.name }}
Write a concise 2–5 sentence description in Markdown.""",
        "column.md.j2": """You are documenting a dbt model column for data analysts.
Model: {{ model.name }}
Column: {{ column.name }}
Write 1–2 crisp sentences.""",
    }
    for name, content in defaults.items():
        p = target / name
        if not p.exists():
            p.write_text(content.strip() + "\n")
    console.print(f"[green]Initialized prompts at {target}[/green]")


@app.command()
def list(
    project_dir: Path = typer.Option(".", help="dbt project dir"),
    target_dir: Path = typer.Option("target", help="dbt target dir"),
    select: str = typer.Option("", help="model patterns, comma-separated (supports glob-like, and +model for parents)"),
    exclude: str = typer.Option("", help="exclude patterns"),
    tags: str = typer.Option("", help="only models with these tags (comma-separated)"),
):
    """
    List dbt models from a manifest with optional selection filters.

    Loads ``target/manifest.json`` and displays models that match selection,
    exclusion, and tag filters.

    Parameters
    ----------
    project_dir : Path
        Path to the dbt project directory.
    target_dir : Path
        Directory containing ``manifest.json`` (usually ``target``).
    select : str
        Comma-separated model selection patterns (supports ``+model`` for parents).
    exclude : str
        Comma-separated exclusion patterns.
    tags : str
        Comma-separated list of required tags.
    """
    project_dir = coerce_path(project_dir)
    target_dir = coerce_path(target_dir)
    manifest = load_manifest(target_dir)
    nodes = list_model_nodes(manifest)

    sel = [s.strip() for s in select.split(",") if s.strip()]
    exc = [s.strip() for s in exclude.split(",") if s.strip()]
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    chosen = select_models(nodes, sel, exc, tag_list) if (sel or exc or tag_list) else nodes

    table = Table(title="dbt models")
    table.add_column("name")
    table.add_column("resource_path")
    table.add_column("tags")

    for n in sorted(chosen, key=lambda x: x["name"]):
        table.add_row(n["name"], n.get("path", ""), ", ".join(n.get("tags") or []))
    console.print(table)


@app.command()
def llm_docs_generate(
    project_dir: Path = typer.Option(".", help="dbt project dir"),
    target_dir: Path = typer.Option("target", help="dbt target dir"),
    backend: str = typer.Option("ollama", help="llm backend (MVP: only 'ollama')"),
    model: str = typer.Option("llama3.1:8b-instruct-q8_0", help="ollama model name"),
    select: str = typer.Option("", help="model patterns, comma-separated"),
    exclude: str = typer.Option("", help="exclude patterns"),
    tags: str = typer.Option("", help="filter by tags"),
    #write: str = typer.Option("schema", help="schema|docs (MVP supports schema)"),
    overwrite: bool = typer.Option(False, help="overwrite existing descriptions"),
    dry_run: bool = typer.Option(False, help="preview changes only"),
    schema_path: str = typer.Option(None, help="explicit schema.yml path for all writes (optional)"),
    ollama_host: str = typer.Option(None, help="override OLLAMA_HOST, e.g., http://localhost:11434"),
    use_data: str = typer.Option(None, help="use data from db, e.g., Y or N"),
):
    """
    Generate dbt model and column documentation via an LLM backend.

    This command reads ``manifest.json`` to locate models, renders Jinja2
    prompt templates for each model and its columns, and sends them to the
    selected LLM backend (currently only Ollama). The returned text is then
    written into corresponding ``schema.yml`` files so that it appears in
    ``dbt docs serve``.

    Parameters
    ----------
    project_dir : Path
        Path to the dbt project directory.
    target_dir : Path
        Directory containing the dbt ``manifest.json`` file.
    backend : str
        LLM backend to use (only ``ollama`` supported in MVP).
    model : str
        Model name or identifier for the LLM (e.g., ``llama3.1:8b-instruct-q8_0``).
    select : str
        Comma-separated model selection patterns.
    exclude : str
        Comma-separated exclusion patterns.
    tags : str
        Comma-separated tag filter.
    write : str
        Destination type (``schema`` or ``docs``). Only ``schema`` is implemented.
    overwrite : bool
        Whether to replace existing descriptions.
    dry_run : bool
        If True, preview generated text without writing to disk.
    schema_path : str
        Optional explicit path to a single ``schema.yml`` file for output.
    ollama_host : str
        Host URL for a remote Ollama instance (default reads ``OLLAMA_HOST`` env var).
    """
    project_dir = coerce_path(project_dir)
    target_dir = coerce_path(target_dir)
    schema_path = coerce_path(schema_path) if schema_path is not None else None

    manifest = load_manifest(target_dir)
    catalog = load_catalog(target_dir)
    nodes = list_model_nodes(manifest)

    

    # Continue to prompt generation…

    sel = [s.strip() for s in select.split(",") if s.strip()]
    exc = [s.strip() for s in exclude.split(",") if s.strip()]
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    chosen = select_models(nodes, sel, exc, tag_list) if (sel or exc or tag_list) else nodes
    if not chosen:
        console.print("[yellow]No models matched selection[/yellow]")
        raise typer.Exit(code=0)

    if backend=='ollama':
        llm = OllamaBackend()
    elif backend=='open-ai':
        llm = OpenAIBackend()
    else:
        console.print("[red]Only 'ollama' backend is supported in MVP[/red]")
        raise typer.Exit(1)
    

    env = _env(Path(project_dir))
    model_tpl = env.get_template("model.md.j2")
    col_tpl = env.get_template("column.md.j2")
    profiles = load_profiles_yml(path=project_dir)
    for node in chosen:
        
        model_name = node["name"]
        relation = node.get("relation_name")
        cols = columns_from_catalog(node, catalog)
        tags = node.get("tags") or []
        sql=node.get('compiled_code')

        if use_data == 'Y':
    # 1. Load profiles.yml from dbt project dir (or join ~/.dbt if needed)
            if profiles is None:
                console.print("[red]profiles.yml not found. Cannot run data profiling.[/red]")
                sys.exit(1)
            available_profiles = profiles
            if not available_profiles:
                console.print("[red]profiles.yml contains no profiles.[/red]")
                sys.exit(1)
            profile_name = next(iter(profiles.keys()))
            console.print(f"[green]Using profile:[/green] {profile_name}")
            console.print(f"[green]Target:[/green] dev")
            # 3. Create db client (reads profiles.yml + dev target)
            db = database_connector.MultiDBClient(
                profiles_path=project_dir,  # path to profiles.yml
                target="dev"
            )
            # 4. Extract the SQL from the manifest node
            if not sql:
                console.print(f"[yellow]No SQL found for model {model_name}. Skipping data profiling.[/yellow]")
                sys.exit(0)
            # 5. Run lightweight pandas profiling
            console.print("[cyan]Profiling sample data…[/cyan]")
            profile_summary = db.profile_query_for_llm(
                kind=profile_name,   # profile name matches DBKind
                sql=sql,
                sample_rows=5000
            )
            
            model_prompt = model_tpl.render(
            model={"name": model_name, "relation_name": relation, "tags": tags, "columns": cols.keys(), "sql": sql,"profile_summary":profile_summary}
        )
            
            column_prompts, col_order = [], []
            for cname, cmeta in cols.items():
                col_profile = pick_column_profile(profile_summary, cname)
                
                col_order.append(cname)
                column_prompts.append(
                    col_tpl.render(model={"name": model_name}, column={"name": cname, "type": cmeta.get("data_type"),"profile_summary":col_profile})
                )        
        else:
            model_prompt = model_tpl.render(
                model={"name": model_name, "relation_name": relation, "tags": tags, "columns": cols.keys(), "sql": sql}
            )
            column_prompts, col_order = [], []
            column_descs = {}
            for cname, cmeta in cols.items():
                col_order.append(cname)
                column_prompts.append(
                    col_tpl.render(model={"name": model_name}, column={"name": cname, "type": cmeta.get("data_type")})
                )


        console.rule(f"[bold cyan]{model_name}")

        with Live(Spinner("dots", text=f"Generating docs for [bold]{model_name}[/bold]..."), refresh_per_second=10):
            model_desc_iter = llm.generate([model_prompt])
            model_desc = next(model_desc_iter)
            if use_data == 'Y':
                column_descs = {}
                for cname, text in zip(col_order, llm.generate(column_prompts)):
    # text = LLM description for this column
                    col_profile = pick_column_profile(profile_summary, cname)  # from earlier helper

                    if col_profile:
                        stats_md = format_column_stats_md(col_profile)
                        full_desc = f"{text.strip()}\n{stats_md}"
                    else:
                        full_desc = text.strip()

                    column_descs[cname] = full_desc
            else:
                column_descs = {cname: text for cname, text in zip(col_order, llm.generate(column_prompts))}
            
        if dry_run:
            console.print("[magenta]Model description:[/magenta]")
            console.print(model_desc)
            console.print("[magenta]Column descriptions (first 5):[/magenta]")
            for i, (k, v) in enumerate(column_descs.items()):
                if i >= 5:
                    console.print("... (truncated)")
                    break
                console.print(f"[bold]{k}[/bold]: {v}")
            continue

        if schema_path:
            schema_file = Path(schema_path)
        else:
            model_rel_path = Path(node.get("original_file_path") or node.get("path") or "models/")
            schema_file = Path(project_dir) / model_rel_path.parts[0] / "schema.yml"

        write_schema_descriptions(schema_file, model_name, model_desc, column_descs, overwrite=overwrite)
        console.print(f"[green]Updated {schema_file}[/green]")


if __name__ == "__main__":
    app()