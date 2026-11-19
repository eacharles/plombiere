"""ORM tables for CECI pipeline, variant, and instance records."""

import uuid
from datetime import date

from pydantic import BaseModel
from sqlalchemy import Date, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from tisserande.db.base import Base
from tisserande.db.graphs import Graph

from .. import models


class CeciPipelineTable(Base):
    """ORM table for CECI pipeline definitions."""

    __tablename__ = "ceci_pipeline"

    id_: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True, unique=True)
    version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    structure: Mapped[dict] = mapped_column(JSON, default=dict)
    config: Mapped[dict] = mapped_column(JSON, default=dict)

    @classmethod
    def pydantic_create_class(cls) -> type[BaseModel]:
        return models.CeciPipelineCreate

    @classmethod
    def pydantic_model_class(cls) -> type[BaseModel]:
        return models.CeciPipeline

    @classmethod
    def class_string(cls) -> str:
        return cls.__tablename__


class CeciPipelineVariantTable(Base):
    """ORM table for CECI pipeline variants."""

    __tablename__ = "ceci_pipeline_variant"

    id_: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_description: Mapped[str] = mapped_column(Text, default="")
    overrides: Mapped[dict] = mapped_column(JSON, default=dict)
    ceci_pipeline_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ceci_pipeline.id_"),
        nullable=False,
        index=True,
    )

    @classmethod
    def pydantic_create_class(cls) -> type[BaseModel]:
        return models.CeciPipelineVariantCreate

    @classmethod
    def pydantic_model_class(cls) -> type[BaseModel]:
        return models.CeciPipelineVariant

    @classmethod
    def class_string(cls) -> str:
        return cls.__tablename__


class CeciPipelineInstanceTable(Graph):
    """ORM subtable for CECI pipeline execution instances.

    Extends Graph via 2-level joined-table inheritance: graph → ceci_pipeline_instance.
    Shared execution fields (status, start_time, end_time, hostname, user,
    environment_json) live on the base graph table.
    """

    __tablename__ = "ceci_pipeline_instance"
    __mapper_args__ = {"polymorphic_identity": "ceci_pipeline_instance"}

    uid_: Mapped[uuid.UUID] = mapped_column(ForeignKey("graph.uid_"), primary_key=True)
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    ceci_pipeline_variant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ceci_pipeline_variant.id_"),
        nullable=False,
        index=True,
    )

    @classmethod
    def pydantic_create_class(cls) -> type[BaseModel]:
        return models.CeciPipelineInstanceCreate

    @classmethod
    def pydantic_model_class(cls) -> type[BaseModel]:
        return models.CeciPipelineInstance

    @classmethod
    def class_string(cls) -> str:
        return cls.__tablename__
