"""
Pre-Alembic Schema Adoption & Parity Verification Module (CIAPI-L003)

Safely adopts pre-existing current-model databases that were initialized
without Alembic version tracking (e.g., via Base.metadata.create_all).

Enforces:
1. Strict schema parity check before any stamping operation:
   - All 11 current-model tables present
   - Column presence, extra unexpected columns detection
   - Column-level type affinity and bidirectional nullability
   - Primary key constraints
   - Exact ordered foreign key mappings (constrained cols -> referred table & cols)
   - Unique constraints and index uniqueness matching
2. Refusal if database is already version-managed by Alembic (fail closed).
3. Refusal if tables are missing, drifted, or if database is uninitialized empty schema.
4. Preserves connection credentials internally with safe percent-encoding handling.
5. Pinned atomic stamping specifically to BASELINE_REVISION ('0001_initial_schema').
"""
from typing import Any, Dict, List, Tuple
from alembic import command
from sqlalchemy import UniqueConstraint, inspect
from sqlalchemy.engine import Engine

from app.database.migration_check import (
    get_alembic_config,
    get_current_revision,
    get_head_revision,
    set_alembic_url_safe,
)
from app.database.session import Base
import app.models  # Ensures all 11 models are registered in Base.metadata

BASELINE_REVISION = "0001_initial_schema"

CURRENT_MODEL_TABLES = [
    "sources",
    "source_health",
    "cancers",
    "cancer_aliases",
    "source_documents",
    "content_records",
    "content_sources",
    "content_versions",
    "ingestion_jobs",
    "consensus_facts",
    "consensus_fact_sources",
]


class SchemaParityError(Exception):
    """Raised when existing database schema does not match Base.metadata or is ineligible for adoption."""
    pass


def verify_schema_parity(engine: Engine) -> Dict[str, Any]:
    """
    Verifies that the target database schema matches Base.metadata definitions
    across all 11 current-model tables.
    Checks:
    - Table presence (all 11 tables must exist)
    - Column presence and detection of unexpected extra columns
    - Column type compatibility (type affinity)
    - Bidirectional column nullability (NOT NULL vs NULLABLE)
    - Primary key constraints
    - Exact ordered foreign key mappings (constrained cols, referred table, referred cols)
    - Unique constraints and declared model indexes including uniqueness

    Raises:
        SchemaParityError: If tables are missing or columns/types/keys/indexes differ.
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    # 1. Check for absence of all current-model tables
    found_current_tables = [t for t in CURRENT_MODEL_TABLES if t in existing_tables]
    if not found_current_tables:
        raise SchemaParityError(
            "Adoption rejected: No current-model tables found in database. "
            "Database is uninitialized. Run 'alembic upgrade head' instead of adoption."
        )

    # 2. Check for missing tables
    missing_tables = [t for t in CURRENT_MODEL_TABLES if t not in existing_tables]
    if missing_tables:
        raise SchemaParityError(
            f"Adoption rejected: Incomplete current-model schema detected. "
            f"Missing required tables: {missing_tables}. Cannot safely adopt drifted schema."
        )

    # 3. Comprehensive column, type, nullability, PK, FK, and index parity
    discrepancies: List[str] = []
    table_reports: Dict[str, Any] = {}

    for tbl_name in CURRENT_MODEL_TABLES:
        model_table = Base.metadata.tables.get(tbl_name)
        if model_table is None:
            discrepancies.append(f"Model definition missing in Base.metadata for table '{tbl_name}'")
            continue

        model_cols = {c.name: c for c in model_table.columns}
        db_cols = {c["name"]: c for c in inspector.get_columns(tbl_name)}

        # A1. Missing columns in DB
        missing_cols = set(model_cols.keys()) - set(db_cols.keys())
        if missing_cols:
            discrepancies.append(
                f"Table '{tbl_name}' is missing expected columns: {sorted(list(missing_cols))}"
            )

        # A2. Unexpected extra columns in DB
        extra_cols = set(db_cols.keys()) - set(model_cols.keys())
        if extra_cols:
            discrepancies.append(
                f"Table '{tbl_name}' contains unexpected extra columns: {sorted(list(extra_cols))}"
            )

        # B. Column type affinity and bidirectional nullability checks
        for c_name, m_col in model_cols.items():
            if c_name in db_cols:
                d_col = db_cols[c_name]
                m_aff = getattr(m_col.type, "_type_affinity", None)
                d_aff = getattr(d_col["type"], "_type_affinity", None)
                if m_aff is not None and d_aff is not None and m_aff != d_aff:
                    discrepancies.append(
                        f"Table '{tbl_name}.{c_name}' type mismatch: expected {m_aff}, found {d_aff}"
                    )
                if not m_col.primary_key:
                    # Model NOT NULL vs DB NULLABLE
                    if not m_col.nullable and d_col["nullable"]:
                        discrepancies.append(
                            f"Table '{tbl_name}.{c_name}' nullability mismatch: expected NOT NULL, found NULLABLE"
                        )
                    # Model NULLABLE vs DB NOT NULL
                    elif m_col.nullable and not d_col["nullable"]:
                        discrepancies.append(
                            f"Table '{tbl_name}.{c_name}' nullability mismatch: expected NULLABLE, found NOT NULL"
                        )

        # C. Primary key parity
        db_pk = inspector.get_pk_constraint(tbl_name).get("constrained_columns", [])
        model_pk = [c.name for c in model_table.primary_key.columns]
        if set(db_pk) != set(model_pk):
            discrepancies.append(
                f"Table '{tbl_name}' primary key mismatch: expected {model_pk}, found {db_pk}"
            )

        # D. Ordered Foreign key mappings
        db_fks = inspector.get_foreign_keys(tbl_name)
        for fk in model_table.foreign_key_constraints:
            m_constrained = [col.name for col in fk.columns]
            m_ref_tbl = fk.referred_table.name
            m_ref_cols = [elem.column.name for elem in fk.elements]
            match = False
            for d_fk in db_fks:
                if list(d_fk["constrained_columns"]) == m_constrained and d_fk["referred_table"] == m_ref_tbl:
                    d_ref = list(d_fk.get("referred_columns") or [])
                    if not d_ref or d_ref == m_ref_cols:
                        match = True
                        break
            if not match:
                discrepancies.append(
                    f"Table '{tbl_name}' missing ordered foreign key mapping: {m_constrained} -> {m_ref_tbl}({m_ref_cols})"
                )

        # E. Unique constraints
        db_unique = [tuple(sorted(uc["column_names"])) for uc in inspector.get_unique_constraints(tbl_name)]
        for c in model_table.constraints:
            if isinstance(c, UniqueConstraint):
                m_u_cols = tuple(sorted([col.name for col in c.columns]))
                if m_u_cols not in db_unique:
                    discrepancies.append(
                        f"Table '{tbl_name}' missing unique constraint on columns {m_u_cols}"
                    )

        # F. Index parity and index uniqueness
        db_indexes = inspector.get_indexes(tbl_name)
        db_idx_map = {tuple(idx["column_names"]): idx for idx in db_indexes if idx.get("column_names")}
        for m_idx in model_table.indexes:
            m_cols = tuple([c.name for c in m_idx.columns])
            if m_cols not in db_idx_map:
                discrepancies.append(
                    f"Table '{tbl_name}' missing declared index covering columns {m_cols}"
                )
            else:
                d_idx = db_idx_map[m_cols]
                if bool(d_idx.get("unique")) != bool(m_idx.unique):
                    discrepancies.append(
                        f"Table '{tbl_name}' index {m_cols} uniqueness mismatch: model={m_idx.unique}, db={d_idx.get('unique')}"
                    )

        table_reports[tbl_name] = {
            "columns_verified": len(db_cols),
            "primary_key": db_pk,
            "foreign_keys_verified": len(db_fks),
            "indexes_verified": len(db_indexes),
        }

    if discrepancies:
        formatted_errors = "\n  - " + "\n  - ".join(discrepancies)
        raise SchemaParityError(
            f"Schema parity verification failed with {len(discrepancies)} discrepancy(ies):{formatted_errors}"
        )

    return {
        "parity_verified": True,
        "tables_verified": len(table_reports),
        "details": table_reports,
    }


def adopt_existing_schema(engine: Engine, dry_run: bool = False) -> Dict[str, Any]:
    """
    Safely adopts an unversioned pre-Alembic database into Alembic version control.

    1. Refuses if database is already managed by Alembic at any revision (fail closed).
    2. Verifies complete schema parity across all 11 tables (types, bidirectional nullability, PKs, FKs, indexes).
    3. Stamps database explicitly to BASELINE_REVISION ('0001_initial_schema').
    """
    current_rev = get_current_revision(engine)

    # Fail closed: reject already-versioned databases
    if current_rev is not None:
        raise SchemaParityError(
            f"Adoption rejected: Database is already managed by Alembic at revision '{current_rev}'. "
            f"Schema adoption is strictly reserved for unversioned baseline databases without an 'alembic_version' table. "
            f"Use 'alembic upgrade head' to apply migrations."
        )

    # Step 1: Verify Parity across all 11 tables
    parity_result = verify_schema_parity(engine)

    if dry_run:
        return {
            "status": "PARITY_VERIFIED_DRY_RUN",
            "current_revision": None,
            "target_baseline_revision": BASELINE_REVISION,
            "tables_verified": parity_result["tables_verified"],
            "message": (
                f"Schema parity confirmed for all {parity_result['tables_verified']} tables. "
                f"Ready to safely adopt unversioned database by stamping to baseline revision '{BASELINE_REVISION}'."
            ),
        }

    # Step 2: Stamp explicitly to pinned BASELINE_REVISION
    cfg = get_alembic_config()
    raw_url = engine.url.render_as_string(hide_password=False)
    set_alembic_url_safe(cfg, raw_url)
    command.stamp(cfg, BASELINE_REVISION)

    post_rev = get_current_revision(engine)
    if post_rev != BASELINE_REVISION:
        raise RuntimeError(
            f"Adoption stamping failed: expected baseline revision '{BASELINE_REVISION}', found '{post_rev}'"
        )

    return {
        "status": "SUCCESSFULLY_ADOPTED",
        "adopted_revision": post_rev,
        "tables_verified": parity_result["tables_verified"],
        "message": f"Database successfully adopted into Alembic at baseline revision '{post_rev}' without table mutation.",
    }
