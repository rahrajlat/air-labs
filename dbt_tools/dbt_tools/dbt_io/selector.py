import fnmatch
from typing import List, Dict, Any, Set, Tuple


def match_name(name: str, patterns: List[str]) -> bool:
    """
    Check if a model name matches any of the given glob-style patterns.

    This helper uses Python's built-in `fnmatch` to support Unix-style wildcards,
    such as `stg_*` or `*_customers`.

    Parameters
    ----------
    name : str
        The dbt model name to test (e.g., "stg_orders").
    patterns : List[str]
        A list of glob-style pattern strings.

    Returns
    -------
    bool
        True if the name matches at least one pattern, False otherwise.
    """
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def _parent_names_from_node(node: Dict[str, Any]) -> list[str]:
    """
    Extract the parent model names from a dbt manifest node.

    The function looks into the `depends_on.nodes` field of the node and collects
    any parent model names. Each dependency string typically has the form
    "model.<project>.<model_name>", so this method strips the prefix and returns
    only the model names.

    Parameters
    ----------
    node : Dict[str, Any]
        A single node dictionary from the dbt manifest.

    Returns
    -------
    list[str]
        List of parent model names referenced by this node.
    """
    out = []
    for key in (node.get("depends_on", {}) or {}).get("nodes", []) or []:
        if isinstance(key, str) and key.startswith("model."):
            out.append(key.split(".")[-1])
    return out


def _build_graph(
    nodes: List[Dict[str, Any]]
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Set[str]], Dict[str, Set[str]]]:
    """
    Build lookup structures for parent/child relationships between dbt models.

    Constructs three mappings:
      - `name_map`:  model_name → node dictionary
      - `parents`:   model_name → set of parent model names
      - `children`:  model_name → set of child model names (reverse of parents)

    These maps make it easier to perform one-hop traversal when expanding
    selections using `+model` (for parents) or `model+` (for children).

    Parameters
    ----------
    nodes : List[Dict[str, Any]]
        List of dbt manifest nodes representing models.

    Returns
    -------
    Tuple[Dict[str, Dict[str, Any]], Dict[str, Set[str]], Dict[str, Set[str]]]
        (name_map, parents, children)
    """
    name_map = {n["name"]: n for n in nodes}
    parents: Dict[str, Set[str]] = {n["name"]: set() for n in nodes}
    children: Dict[str, Set[str]] = {n["name"]: set() for n in nodes}

    # Build parent relationships
    for n in nodes:
        n_name = n["name"]
        for p in _parent_names_from_node(n):
            if p in parents:
                parents[n_name].add(p)

    # Invert the parent mapping to get children
    for child, ps in parents.items():
        for p in ps:
            if p in children:
                children[p].add(child)

    return name_map, parents, children


def _parse_token(token: str) -> Tuple[str, bool, bool]:
    """
    Parse a dbt-style model selection token to determine relationship flags.

    Supports tokens such as:
      - "+foo"   → include `foo` and its parents
      - "foo+"   → include `foo` and its children
      - "+foo+"  → include `foo`, parents, and children
      - "foo"    → include only `foo`

    Parameters
    ----------
    token : str
        The raw selection token string.

    Returns
    -------
    Tuple[str, bool, bool]
        (base_name, want_parents, want_children)
        - `base_name`: The core model name without `+`.
        - `want_parents`: True if token starts with '+'.
        - `want_children`: True if token ends with '+'.
    """
    want_parents = token.startswith("+")
    want_children = token.endswith("+")
    base = token.strip("+")
    return base, want_parents, want_children


def select_models(
    nodes: List[Dict[str, Any]],
    select: List[str],
    exclude: List[str],
    tags: List[str],
) -> List[Dict[str, Any]]:
    """
    Select dbt models from a manifest using name patterns, tags, and adjacency operators.

    Implements simplified dbt selection syntax:
      - Plain patterns (`orders_*`) match model names via glob rules.
      - `+model` adds the model and its **parents** (one hop).
      - `model+` adds the model and its **children** (one hop).
      - `+model+` adds both parents and children.
      - `--tags` limits matches to models containing one or more of the provided tags.
      - `--exclude` removes models matching exclusion patterns.

    Parameters
    ----------
    nodes : List[Dict[str, Any]]
        List of dbt model node dictionaries from the manifest.
    select : List[str]
        List of model selection tokens (patterns or +model syntax).
    exclude : List[str]
        List of model exclusion patterns.
    tags : List[str]
        List of tag names to filter by.

    Returns
    -------
    List[Dict[str, Any]]
        Sorted list of selected model node dictionaries.

    Notes
    -----
    - Only **one-hop** parent/child expansion is supported.
    - If no filters are provided, all nodes are returned unchanged.
    - Models not found in the manifest are silently ignored.
    """
    if not (select or exclude or tags):
        return nodes

    name_map, parents, children = _build_graph(nodes)
    selected: Set[str] = set()
    direct_patterns: List[str] = []
    plus_bases: List[Tuple[str, bool, bool]] = []

    # Split tokens into pattern and +model variants
    for token in select:
        token = token.strip()
        if not token:
            continue
        if token.startswith("+") or token.endswith("+"):
            base, wp, wc = _parse_token(token)
            if base in name_map:
                plus_bases.append((base, wp, wc))
        else:
            direct_patterns.append(token)

    # Match glob patterns
    if direct_patterns:
        for n in nodes:
            if match_name(n["name"], direct_patterns):
                selected.add(n["name"])

    # Handle +base tokens (parents/children)
    for base, wp, wc in plus_bases:
        selected.add(base)
        if wp:
            selected.update(parents.get(base, ()))
        if wc:
            selected.update(children.get(base, ()))

    # Tag filtering
    if tags:
        selected = {
            n for n in selected
            if set(name_map[n].get("tags") or []).intersection(tags)
        }

    # Exclude filtering
    if exclude:
        selected = {n for n in selected if not match_name(n, exclude)}

    return [name_map[n] for n in sorted(selected)] if selected else []