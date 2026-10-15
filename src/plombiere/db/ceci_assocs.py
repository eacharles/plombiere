"""ORM table for CECI pipeline-to-stage associations."""

import uuid

from pydantic import BaseModel
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from tisserande.db.base import Base

from .. import models


class CeciPipelineStageAssocTable(Base):
    """Association between a CeciPipeline and a schema-level CeciStageNode."""

    __tablename__ = "ceci_pipeline_stage_assoc"

    id_: Mapped[int] = mapped_column(primary_key=True)
    ceci_pipeline_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ceci_pipeline.id_"),
        nullable=False,
        index=True,
    )
    ceci_stage_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("node.id_"),
        nullable=False,
        index=True,
    )

    @classmethod
    def pydantic_create_class(cls) -> type[BaseModel]:
        return models.CeciPipelineStageAssocCreate

    @classmethod
    def pydantic_model_class(cls) -> type[BaseModel]:
        return models.CeciPipelineStageAssoc

    @classmethod
    def class_string(cls) -> str:
        return cls.__tablename__
