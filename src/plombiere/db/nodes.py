"""ORM tables for CECI-specific node types, extending tisserande's node hierarchy."""

import uuid

from pydantic import BaseModel
from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from tisserande.db.nodes import DataFileNodeTable, NodeTable
from tisserande.db_oper.nodes import register_node_type

from .. import models


class CeciFileNodeTable(DataFileNodeTable):
    """ORM table for CECI file nodes.

    Extends DataFileNodeTable via 3-level joined-table inheritance:
    node → data_file_node → ceci_file_node.
    """

    __tablename__ = "ceci_file_node"
    __mapper_args__ = {"polymorphic_identity": "ceci_file"}

    id_: Mapped[uuid.UUID] = mapped_column(ForeignKey("data_file_node.id_"), primary_key=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    data_registry_id: Mapped[int | None] = mapped_column(nullable=True)
    ceci_file_schema_node_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ceci_file_node.id_"),
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


class CeciStageNodeTable(NodeTable):
    """ORM table for CECI stage nodes."""

    __tablename__ = "ceci_stage_node"
    __mapper_args__ = {"polymorphic_identity": "ceci_stage"}

    id_: Mapped[uuid.UUID] = mapped_column(ForeignKey("node.id_"), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    python_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    overrides: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    data_registry_id: Mapped[int | None] = mapped_column(nullable=True)
    ceci_stage_schema_node_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ceci_stage_node.id_"),
        nullable=True,
    )

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
