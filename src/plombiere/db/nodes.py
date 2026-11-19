"""ORM tables for CECI-specific node types, extending tisserande's node hierarchy."""

import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from tisserande.db.data_types import DataFileType
from tisserande.db.function_types import ShellFunction
from tisserande.db.nodes import DataFile, Node
from tisserande.db_oper.nodes import register_node_type

from .. import models


class CeciFileTable(DataFile):
    """ORM table for CECI file nodes.

    Extends DataFile via 3-level joined-table inheritance:
    node → data_file → ceci_file.
    """

    __tablename__ = "ceci_file"
    __mapper_args__ = {"polymorphic_identity": "ceci_file"}

    uid_: Mapped[uuid.UUID] = mapped_column(ForeignKey("data_file.uid_"), primary_key=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    data_registry_id: Mapped[int | None] = mapped_column(nullable=True)

    @classmethod
    def pydantic_create_class(cls) -> type[BaseModel]:
        return models.CeciFileCreate

    @classmethod
    def pydantic_model_class(cls) -> type[BaseModel]:
        return models.CeciFile

    @classmethod
    def class_string(cls) -> str:
        return "ceci_file"


class CeciStageCallTable(Node):
    """ORM table for CECI stage nodes."""

    __tablename__ = "ceci_stage_call"
    __mapper_args__ = {"polymorphic_identity": "ceci_stage_call"}

    uid_: Mapped[uuid.UUID] = mapped_column(ForeignKey("node.uid_"), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    python_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    overrides: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    data_registry_id: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    @classmethod
    def pydantic_create_class(cls) -> type[BaseModel]:
        return models.CeciStageCallCreate

    @classmethod
    def pydantic_model_class(cls) -> type[BaseModel]:
        return models.CeciStageCall

    @classmethod
    def class_string(cls) -> str:
        return "ceci_stage_call"


register_node_type("ceci_file", CeciFileTable, models.CeciFileCreate)
register_node_type("ceci_stage_call", CeciStageCallTable, models.CeciStageCallCreate)


class CeciFileTypeTable(DataFileType):
    """ORM table for the CeciFileType node template sub-type.

    Extends DataFileType via 3-level joined-table inheritance:
    node_template → data_file_type → ceci_file_node_type.
    """

    __tablename__ = "ceci_file_type"
    __mapper_args__ = {"polymorphic_identity": "ceci_file_type"}

    id_: Mapped[int] = mapped_column(ForeignKey("data_file_type.id_"), primary_key=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    @classmethod
    def pydantic_create_class(cls) -> type[BaseModel]:
        return models.CeciFileTypeCreate

    @classmethod
    def pydantic_model_class(cls) -> type[BaseModel]:
        return models.CeciFileType

    @classmethod
    def class_string(cls) -> str:
        return cls.__tablename__


class CeciStageTable(ShellFunction):
    """ORM table for the CeciStage node template sub-type.

    Extends ShellFunction via 3-level joined-table inheritance:
    node_template → shell_function → ceci_stage.
    """

    __tablename__ = "ceci_stage"
    __mapper_args__ = {"polymorphic_identity": "ceci_stage"}

    id_: Mapped[int] = mapped_column(ForeignKey("shell_function.id_"), primary_key=True)
    python_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    @classmethod
    def pydantic_create_class(cls) -> type[BaseModel]:
        return models.CeciStageCreate

    @classmethod
    def pydantic_model_class(cls) -> type[BaseModel]:
        return models.CeciStage

    @classmethod
    def class_string(cls) -> str:
        return cls.__tablename__
