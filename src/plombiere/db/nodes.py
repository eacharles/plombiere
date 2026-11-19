"""ORM tables for CECI-specific node types, extending tisserande's node hierarchy."""

import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from tisserande.db.nodes import Node
from tisserande.db_oper.nodes import register_node_type

from .. import models


class CeciFileNodeTable(Node):
    """ORM table for CECI file nodes.

    Extends Node via 2-level joined-table inheritance: node → ceci_file_node.
    """

    __tablename__ = "ceci_file_node"
    __mapper_args__ = {"polymorphic_identity": "ceci_file"}

    uid_: Mapped[uuid.UUID] = mapped_column(ForeignKey("node.uid_"), primary_key=True)
    creator: Mapped[str] = mapped_column(String(255), default="ceci")
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    data_registry_id: Mapped[int | None] = mapped_column(nullable=True)
    ceci_file_schema_node_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ceci_file_node.uid_"),
        nullable=True,
    )

    @classmethod
    def pydantic_create_class(cls) -> type[BaseModel]:
        return models.CeciFileNodeCreate

    @classmethod
    def pydantic_model_class(cls) -> type[BaseModel]:
        return models.CeciFileNode

    @classmethod
    def class_string(cls) -> str:
        return "ceci_file_node"


class CeciStageNodeTable(Node):
    """ORM table for CECI stage nodes."""

    __tablename__ = "ceci_stage_node"
    __mapper_args__ = {"polymorphic_identity": "ceci_stage"}

    uid_: Mapped[uuid.UUID] = mapped_column(ForeignKey("node.uid_"), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    python_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    overrides: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    data_registry_id: Mapped[int | None] = mapped_column(nullable=True)
    ceci_stage_schema_node_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ceci_stage_node.uid_"),
        nullable=True,
    )
    ceci_pipeline_instance_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ceci_pipeline_instance.id_"),
        nullable=True,
        index=True,
    )
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    @classmethod
    def pydantic_create_class(cls) -> type[BaseModel]:
        return models.CeciStageNodeCreate

    @classmethod
    def pydantic_model_class(cls) -> type[BaseModel]:
        return models.CeciStageNode

    @classmethod
    def class_string(cls) -> str:
        return "ceci_stage_node"


register_node_type("ceci_file", CeciFileNodeTable, models.CeciFileNodeCreate)
register_node_type("ceci_stage", CeciStageNodeTable, models.CeciStageNodeCreate)
