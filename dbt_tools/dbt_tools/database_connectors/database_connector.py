"""
multi_db.py

Multi-database SQL client with Pandas DataFrame output.
Supports Postgres, Redshift, and Snowflake using SQLAlchemy.
Configuration is pulled from dbt's profiles.yml instead of environment variables.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal, Dict, Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from dbt_tools.dbt_io.loader import load_profiles_yml  # adjust import if needed

DBKind = Literal["postgres", "redshift", "snowflake"]


# ---------------------------------------------------------------------
#  Database Configs (from dbt profile outputs)
# ---------------------------------------------------------------------

@dataclass
class PostgresConfig:
    host: str
    port: str
    database: str
    user: str
    password: str

    @classmethod
    def from_profile(cls, cfg: Dict[str, Any]) -> "PostgresConfig":
        """
        Build PostgresConfig from a dbt profile 'output' dict.
        Expected keys (standard dbt-postgres):
            type: postgres
            host, port, dbname/database, user, password
        """
        host = cfg.get("host")
        port = str(cfg.get("port", 5432))
        db = cfg.get("dbname") or cfg.get("database")
        user = cfg.get("user")
        password = cfg.get("password")

        if not all([host, db, user, password]):
            raise ValueError("Incomplete Postgres profile configuration.")

        return cls(host=host, port=port, database=db, user=user, password=password)

    def to_url(self) -> str:
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class RedshiftConfig(PostgresConfig):
    @classmethod
    def from_profile(cls, cfg: Dict[str, Any]) -> "RedshiftConfig":
        """
        Build RedshiftConfig from a dbt profile 'output' dict.
        Expected keys:
            type: redshift
            host, port, dbname/database, user, password
        """
        host = cfg.get("host")
        port = str(cfg.get("port", 5439))
        db = cfg.get("dbname") or cfg.get("database")
        user = cfg.get("user")
        password = cfg.get("password")

        if not all([host, db, user, password]):
            raise ValueError("Incomplete Redshift profile configuration.")

        return cls(host=host, port=port, database=db, user=user, password=password)

    def to_url(self) -> str:
        return f"redshift+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class SnowflakeConfig:
    account: str
    user: str
    password: str
    database: str
    schema: str
    warehouse: str
    role: Optional[str] = None

    @classmethod
    def from_profile(cls, cfg: Dict[str, Any]) -> "SnowflakeConfig":
        """
        Build SnowflakeConfig from a dbt profile 'output' dict.
        Expected keys (dbt-snowflake):
            type: snowflake
            account, user, password, database, schema, warehouse, [role]
        """
        account = cfg.get("account")
        user = cfg.get("user")
        password = cfg.get("password")
        database = cfg.get("database")
        schema = cfg.get("schema")
        warehouse = cfg.get("warehouse")
        role = cfg.get("role")

        if not all([account, user, password, database, schema, warehouse]):
            raise ValueError("Incomplete Snowflake profile configuration.")

        return cls(
            account=account,
            user=user,
            password=password,
            database=database,
            schema=schema,
            warehouse=warehouse,
            role=role,
        )

    def to_url(self) -> str:
        base = f"snowflake://{self.user}:{self.password}@{self.account}/{self.database}/{self.schema}"
        params = f"?warehouse={self.warehouse}"
        if self.role:
            params += f"&role={self.role}"
        return base + params


# ---------------------------------------------------------------------
#  Multi-DB Client (reads from profiles.yml)
# ---------------------------------------------------------------------

class MultiDBClient:
    """
    Creates SQLAlchemy Engines for multiple warehouses and returns query
    results as Pandas DataFrames.

    Configuration is loaded from dbt's profiles.yml. We assume:
      - profile name == kind (e.g. "postgres", "redshift", "snowflake")
      - target == "dev" by default
    """

    def __init__(
        self,
        profiles_path: str | Path | None = None,
        target: str = "dev",
    ) -> None:
        self._profiles = load_profiles_yml(profiles_path)
        if self._profiles is None:
            raise RuntimeError("profiles.yml not found. Ensure it exists or pass a valid path.")

        self._target = target  # yml target is always dev (by default here)
        self._engines: Dict[DBKind, Engine] = {}

    def _get_output_config(self, profile_name: str) -> Dict[str, Any]:
        """
        Fetch the dbt profile 'output' config for a given profile name and target.
        """
        profile = self._profiles.get(profile_name)
        if not profile:
            raise KeyError(f"Profile '{profile_name}' not found in profiles.yml.")

        outputs = profile.get("outputs") or {}
        cfg = outputs.get(self._target)
        if not cfg:
            raise KeyError(
                f"Target '{self._target}' not found in profile '{profile_name}'. "
                "Ensure the target exists in profiles.yml."
            )
        return cfg

    def get_engine(self, kind: DBKind) -> Engine:
        """
        Get (or create) an Engine for the given dbt profile / adapter kind.
        Here, 'kind' doubles as the profile name in profiles.yml.
        """
        if kind in self._engines:
            return self._engines[kind]

        cfg = self._get_output_config(kind)
        adapter_type = cfg.get("type")

        if adapter_type == "postgres":
            pg_cfg = PostgresConfig.from_profile(cfg)
            url = pg_cfg.to_url()

        elif adapter_type == "redshift":
            rs_cfg = RedshiftConfig.from_profile(cfg)
            url = rs_cfg.to_url()

        elif adapter_type == "snowflake":
            sf_cfg = SnowflakeConfig.from_profile(cfg)
            url = sf_cfg.to_url()

        else:
            raise ValueError(f"Unsupported adapter type in profile '{kind}': {adapter_type!r}")

        engine = create_engine(url)
        self._engines[kind] = engine
        return engine

    def query_df(self, kind: DBKind, sql: str) -> pd.DataFrame:
        """
        Execute a SQL query and return a Pandas DataFrame.
        """
        engine = self.get_engine(kind)
        return pd.read_sql(sql=text(sql), con=engine)

    def test_connection(self, kind: DBKind) -> bool:
        engine = self.get_engine(kind)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True

    def profile_query_for_llm(
        self,
        kind: DBKind,
        sql: str,
        sample_rows: int = 5000,
        max_example_values: int = 3,
    ) -> dict:
        """
        Run a query, lightly profile the result with pandas, and return a compact
        dictionary summary suitable for use in an LLM prompt.
        """
        import numpy as np

        df = self.query_df(kind, sql)

        total_rows = int(len(df))
        n_columns = int(df.shape[1])

        if total_rows == 0 or n_columns == 0:
            return {
                "row_count": 0,
                "n_columns": 0,
                "columns": [],
            }

        # Downsample
        if sample_rows and total_rows > sample_rows:
            df_sample = df.sample(sample_rows, random_state=42)
        else:
            df_sample = df

        n_sample = len(df_sample)
        columns_summary: list[dict] = []

        for col_name in df_sample.columns:
            s = df_sample[col_name]
            dtype_str = str(s.dtype)

            missing_pct = float(s.isna().mean())
            unique_pct = float(s.nunique(dropna=True) / n_sample) if n_sample > 0 else 0.0

            non_null_values = s.dropna().unique()
            example_values = []
            for v in non_null_values[:max_example_values]:
                if isinstance(v, (np.generic,)):
                    v = v.item()
                example_values.append(v)

            min_val = max_val = mean_val = std_val = None

            if pd.api.types.is_numeric_dtype(s):
                if s.notna().any():
                    min_val = float(s.min())
                    max_val = float(s.max())
                    mean_val = float(s.mean())
                    std_val = float(s.std())

            elif pd.api.types.is_datetime64_any_dtype(s):
                if s.notna().any():
                    min_val = s.min().isoformat()
                    max_val = s.max().isoformat()

            col_summary = {
                "name": col_name,
                "dtype": dtype_str,
                "missing_pct": missing_pct,
                "unique_pct": unique_pct,
                "min": min_val,
                "max": max_val,
                "mean": mean_val,
                "std": std_val,
                "example_values": example_values,
            }
            columns_summary.append(col_summary)

        return {
            "row_count": total_rows,
            "n_columns": n_columns,
            "sampled_rows": n_sample,
            "columns": columns_summary,
        }