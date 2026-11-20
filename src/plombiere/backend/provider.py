"""Backend provider managing DB initialisation and per-entity ops dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BackendSettings:
    db_url: str = "sqlite+aiosqlite:///plombiere.db"


class _TypeFilteredNodeOps:
    """Wraps tisserande node ops to expose only nodes of one type."""

    def __init__(self, node_ops: Any, type_value: str) -> None:
        self._ops = node_ops
        self._type = type_value

    def get_rows(self, limit: int = 10_000, **kwargs: Any) -> list[Any]:
        return [r for r in self._ops.get_rows(limit=limit, **kwargs) if str(r.node_type) == self._type]

    def count_rows(self) -> int:
        return len(self.get_rows())

    def get_row(self, id_: Any) -> Any:
        return self._ops.get_row(id_)

    def delete_row(self, id_: Any) -> None:
        self._ops.delete_row(id_)


class BackendProvider:
    """Singleton providing tisserande/plombiere ops for the Dash dashboard."""

    _instance: BackendProvider | None = None

    def __init__(self) -> None:
        self._settings = BackendSettings()
        self._initialized = False

    @classmethod
    def get(cls) -> BackendProvider:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    @property
    def settings(self) -> BackendSettings:
        return self._settings

    def configure(self, settings: BackendSettings) -> None:
        self._settings = settings
        self._initialized = False

    def initialize(self) -> None:
        import asyncio
        import sqlalchemy as sa
        from tisserande.db.base import Base, close_db, init_db

        # Close any previously open async engine before reinitialising.
        asyncio.run(close_db())
        init_db(self._settings.db_url)

        # Use a temporary sync engine for DDL only — avoids event-loop conflicts
        # with macon's async engine that init_db() sets up for DML.
        sync_url = self._settings.db_url.replace("+aiosqlite", "")
        engine = sa.create_engine(sync_url)
        Base.metadata.create_all(engine)
        engine.dispose()
        self._initialized = True

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self.initialize()

    def get_ops(self, entity_name: str) -> Any:
        self._ensure_initialized()
        from tisserande import local_sync as ts_sync
        from plombiere import local_sync as pl_sync

        from plombiere.local_sync.node_types import ceci_file_type, ceci_stage

        ops_map: dict[str, Any] = {
            "node": ts_sync.node,
            "edge": ts_sync.edge,
            "association": ts_sync.association,
            "edge_template": ts_sync.edge_template,
            "assoc_template": ts_sync.assoc_template,
            "ceci_file": _TypeFilteredNodeOps(ts_sync.node, "ceci_file"),
            "ceci_stage_call": _TypeFilteredNodeOps(ts_sync.node, "ceci_stage_call"),
            "ceci_stage": ceci_stage,
            "ceci_file_type": ceci_file_type,
            "ceci_pipeline": pl_sync.ceci_pipeline,
            "ceci_pipeline_variant": pl_sync.ceci_pipeline_variant,
            "ceci_pipeline_instance": pl_sync.ceci_pipeline_instance,
        }
        return ops_map[entity_name]
