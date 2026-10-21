"""ORM tables for CECI pipeline, variant, and instance records."""

import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Date, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from tisserande.db.base import Base
from tisserande.db.utils import uuid7 as _uuid7

from .. import models


class CeciPipelineTable(Base):
    """ORM table for CECI pipeline definitions."""

    __tablename__ = "ceci_pipeline"

    id_: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True, unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
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


class CeciPipelineInstanceTable(Base):
    """ORM table for a specific pipeline run."""

    __tablename__ = "ceci_pipeline_instance"

    id_: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_uuid7)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    execution_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True, default=None)
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
