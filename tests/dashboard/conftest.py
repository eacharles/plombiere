"""Fixtures for Dash integration tests.

The autouse `_setup_db` fixture from tests/conftest.py is overridden here with
a no-op so that the module-scoped `dash_db_url` fixture manages the database
lifetime instead of resetting it before every test.
"""

from __future__ import annotations

import asyncio

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

    from plombiere.local_sync import ceci_pipeline as pipeline_ops
    from plombiere.local_sync import ceci_pipeline_variant as variant_ops

    pipeline_row = pipeline_ops.create_row(
        name="test_pipeline",
        description="Test pipeline",
        structure={},
        config={},
    )
    variant_ops.create_row(
        name="test_variant",
        extra_description="",
        overrides={},
        ceci_pipeline_id=pipeline_row.id_,
    )

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
