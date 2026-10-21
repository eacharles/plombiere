"""Fixtures for Dash integration tests.

The autouse `_setup_db` fixture from tests/conftest.py is overridden here with
a no-op so that the module-scoped `dash_db_url` fixture manages the database
lifetime instead of resetting it before every test.
"""

from __future__ import annotations

import asyncio
import textwrap

import pytest

# ---------------------------------------------------------------------------
# Suppress warnings from Selenium / Dash internals that we don't control
# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
    pytest.mark.filterwarnings("ignore::ResourceWarning"),
    pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning"),
    pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning"),
]

# ---------------------------------------------------------------------------
# Override the autouse DB-reset fixture so dashboard tests keep their DB
# ---------------------------------------------------------------------------

_PIPELINE_YAML = textwrap.dedent("""\
    stages:
      - name: ingest
        classname: IngestStage
        module_name: test.pipeline
        aliases:
          output: raw_data
      - name: process
        classname: ProcessStage
        module_name: test.pipeline
        aliases:
          input: raw_data
          output: processed_data
      - name: summarise
        classname: SummariseStage
        module_name: test.pipeline
        aliases:
          input: processed_data
""")

# Synthetic stage log files — one per stage, matching the YAML classnames
_STAGE_LOGS: dict[str, str] = {
    "ingest": textwrap.dedent("""\
        Executing stage: IngestStage @ 2025-01-01 10:00:00.000000
        Inserting handle into data store.  raw_data: inprogress_/data/raw_data.fits, ingest
        Stage complete: IngestStage @ 2025-01-01 10:01:00.000000 took 1.0 minutes
    """),
    "process": textwrap.dedent("""\
        Executing stage: ProcessStage @ 2025-01-01 10:01:00.000000
        Inserting handle into data store.  raw_data: /data/raw_data.fits, process
        Inserting handle into data store.  processed_data: inprogress_/data/processed_data.fits, process
        Stage complete: ProcessStage @ 2025-01-01 10:03:00.000000 took 2.0 minutes
    """),
    "summarise": textwrap.dedent("""\
        Executing stage: SummariseStage @ 2025-01-01 10:03:00.000000
        Inserting handle into data store.  processed_data: /data/processed_data.fits, summarise
        Stage complete: SummariseStage @ 2025-01-01 10:05:00.000000 took 2.0 minutes
    """),
}

_CONFIG_YAML = textwrap.dedent("""\
    ingest:
      batch_size: 100
    process:
      algorithm: fast
""")


@pytest.fixture(autouse=True)
def _setup_db():
    """No-op: dashboard tests use the module-scoped dash_db_url fixture."""
    yield





@pytest.fixture(scope="module")
def dash_db_url(tmp_path_factory):
    """Create a file-backed SQLite DB with one pipeline + one variant."""
    from tisserande.db.base import Base, close_db, init_db

    db_dir = tmp_path_factory.mktemp("dash_db")
    db_path = db_dir / "dash.db"
    url = f"sqlite+aiosqlite:///{db_path}"

    import plombiere  # noqa: F401 — trigger node-type registration

    asyncio.run(close_db())
    init_db(url)

    async def _create_tables():
        from macon.db.session import get_session

        async with get_session() as session:
            conn = await session.connection()
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create_tables())

    yaml_path = db_dir / "pipeline.yaml"
    config_path = db_dir / "config.yaml"
    yaml_path.write_text(_PIPELINE_YAML)
    config_path.write_text(_CONFIG_YAML)

    from plombiere.ceci_ingest import (
        ingest_stage_logs,
        register_pipeline_from_yaml,
        register_pipeline_variant_from_yaml,
    )
    from plombiere.local_sync import ceci_pipeline as pipeline_ops

    pipeline_create, schema_nodes = register_pipeline_from_yaml(yaml_path, name="test_pipeline")
    pipeline_row = pipeline_ops.create_row(**pipeline_create.model_dump())
    variant = register_pipeline_variant_from_yaml(config_path, pipeline_row.id_, name="test_variant")

    # Write synthetic log files and ingest to create a CeciPipelineInstance
    log_dir = db_dir / "logs"
    log_dir.mkdir()
    for stage_name, content in _STAGE_LOGS.items():
        (log_dir / f"{stage_name}.out").write_text(content)

    ingest_stage_logs(log_dir, schema_nodes=schema_nodes, pipeline_variant=variant)

    asyncio.run(close_db())
    return url


@pytest.fixture(scope="module")
def dash_app(dash_db_url):
    """Module-scoped Dash app pointing at the test DB."""
    from plombiere.backend import BackendProvider, BackendSettings

    BackendProvider.reset()
    provider = BackendProvider.get()
    provider.configure(BackendSettings(db_url=dash_db_url))
    provider.initialize()

    from plombiere.dashboard.app import create_app

    app = create_app(debug=False)
    yield app
    BackendProvider.reset()
