"""Pydantic models for ceci pipeline, variant, and instance tables."""

from datetime import date
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from tisserande.models.types import ExecutionStatus


class CeciPipelineBase(BaseModel):
    """Describes a generic pipeline."""

    name: str = Field(..., description="Name of the pipeline")
    description: str = Field(..., description="Description of the pipeline")
    structure: dict = Field(..., description="Contents of the pipeline YAML file")
    config: dict = Field(..., description="Contents of the default pipeline_config.yaml")


class CeciPipelineCreate(CeciPipelineBase):
    """Fields used to create a CeciPipeline."""


class CeciPipeline(CeciPipelineBase):
    """CeciPipeline response model."""

    model_config = ConfigDict(from_attributes=True)
    col_names_for_table: ClassVar[list[str]] = ["id_", "name"]

    id_: int = Field(..., gt=0)


class CeciPipelineVariantBase(BaseModel):
    """Describes a variant of a pipeline."""

    name: str = Field(..., description="Name of the variant")
    extra_description: str = Field(..., description="Additional description for this variant")
    overrides: dict = Field(..., description="Config overrides relative to the base CeciPipeline")
    ceci_pipeline_id: int = Field(..., description="Foreign key into CeciPipeline table")


class CeciPipelineVariantCreate(CeciPipelineVariantBase):
    """Fields used to create a CeciPipelineVariant."""


class CeciPipelineVariant(CeciPipelineVariantBase):
    """CeciPipelineVariant response model."""

    model_config = ConfigDict(from_attributes=True)
    col_names_for_table: ClassVar[list[str]] = ["id_", "name"]

    id_: int = Field(..., gt=0)


class CeciPipelineInstanceBase(BaseModel):
    """Describes an execution instance of a pipeline."""

    status: ExecutionStatus = Field(..., description="Execution status")
    run_date: date = Field(..., description="Execution date")
    ceci_pipeline_variant_id: int = Field(..., description="Foreign key into CeciPipelineVariant table")


class CeciPipelineInstanceCreate(CeciPipelineInstanceBase):
    """Fields used to create a CeciPipelineInstance."""


class CeciPipelineInstance(CeciPipelineInstanceBase):
    """CeciPipelineInstance response model."""

    model_config = ConfigDict(from_attributes=True)
    col_names_for_table: ClassVar[list[str]] = ["id_", "status", "run_date", "ceci_pipeline_variant_id"]

    id_: UUID = Field(...)
