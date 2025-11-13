# dbt_warehouse_demo (with column docs)

This dbt project targets **Postgres** and follows a classic warehouse layout:

- **seeds/** → raw-like data (landed to `stage` schema)
- **models/stage/** → light cleaning & typing
- **models/intermediate/** → business transforms (joins/rollups)
- **models/core/** → 1‑to‑1 copies as presentation layer

Run:
```bash
dbt seed
dbt build
dbt docs generate && dbt docs serve
```

Check the docs site for column descriptions and lineage.