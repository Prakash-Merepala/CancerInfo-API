"""
Alembic Migration Verification Module

Inspects database schema state and verifies that the active database is at the
current Alembic head revision without executing any mutations.
"""
from pathlib import Path
from typing import Optional
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import Engine


def get_alembic_config() -> Config:
    """Load Alembic configuration referencing the repository root alembic.ini."""
    project_root = Path(__file__).resolve().parent.parent.parent
    ini_path = project_root / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(project_root / "alembic"))
    return cfg


def set_alembic_url_safe(config: Config, url_str: str) -> None:
    """
    Sets 'sqlalchemy.url' in Alembic Config safely handling percent-encoded credentials
    by escaping '%' as '%%' to prevent ConfigParser InterpolationSyntaxError.
    """
    config.set_main_option("sqlalchemy.url", url_str.replace("%", "%%"))


def get_head_revision() -> str:
    """Return the expected Alembic head revision identifier."""
    cfg = get_alembic_config()
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()
    if head is None:
        raise RuntimeError("No Alembic head revision found in migration script directory.")
    return head


LEGACY_REVISION_ALIASES = {
    "0002_document_rights_and_consensus_linkage": "0002_document_rights",
}


def get_current_revision(engine: Engine) -> Optional[str]:
    """Inspect the connected database and return its current Alembic version_num, or None."""
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        rev = ctx.get_current_revision()
        if rev in LEGACY_REVISION_ALIASES:
            canonical = LEGACY_REVISION_ALIASES[rev]
            # Transparently remap disposable SQLite/dev databases stamped with legacy long revision
            try:
                conn.execute(
                    text("UPDATE alembic_version SET version_num = :canonical WHERE version_num = :legacy"),
                    {"canonical": canonical, "legacy": rev},
                )
                conn.commit()
            except Exception:
                pass
            return canonical
        return rev


def verify_database_schema_at_head(engine: Engine) -> str:
    """
    Verifies that the database is connected and its schema is at Alembic head revision.
    Raises RuntimeError if the database is unmigrated or at an outdated revision.
    Returns the verified head revision string.
    """
    # 1. Verify connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise RuntimeError(f"Database connectivity check failed: {exc}") from exc

    # 2. Check current vs expected head revision
    head_rev = get_head_revision()
    current_rev = get_current_revision(engine)

    if current_rev is None:
        raise RuntimeError(
            f"Database schema validation failed: Database is uninitialized or unmigrated (no Alembic revisions found). "
            f"Expected head revision: '{head_rev}'. "
            f"Automatic schema creation in production is strictly disabled. "
            f"Run 'alembic upgrade head' before starting the application."
        )

    if current_rev != head_rev:
        raise RuntimeError(
            f"Database schema validation failed: Current database revision is '{current_rev}', "
            f"but expected head revision is '{head_rev}'. "
            f"Run 'alembic upgrade head' before starting the application."
        )

    return head_rev
