"""Pydantic models for ceci pipeline, variant, and instance tables."""

from datetime import date
from typing import ClassVar

from pydantic import Field

from tisserande.models.base import Graph, GraphCreate, GraphTemplate, GraphTemplateCreate


class CeciPipelineMixin:
    """Mixin for a GraphTemplate that describes a CECI pipeline."""

    structure: dict = Field(..., description="Contents of the pipeline YAML file")
    config: dict = Field(..., description="Contents of the default pipeline_config.yaml")


class CeciPipelineCreate(GraphTemplateCreate, CeciPipelineMixin):
    """Fields used to create a CeciPipeline."""


class CeciPipeline(GraphTemplate, CeciPipelineMixin):
    """CeciPipeline response model."""

    col_names_for_table: ClassVar[list[str]] = ["id_", "name", "version"]


class CeciPipelineVariantMixin:
    """Mixin for a GraphTemplate that describes a CECI pipeline variant."""

    extra_description: str = Field(..., description="Additional description for this variant")
    overrides: dict = Field(..., description="Config overrides relative to the base CeciPipeline")
    ceci_pipeline_id: int = Field(..., description="Foreign key into CeciPipeline table")


class CeciPipelineVariantCreate(GraphTemplateCreate, CeciPipelineVariantMixin):
    """Fields used to create a CeciPipelineVariant."""


class CeciPipelineVariant(GraphTemplate, CeciPipelineVariantMixin):
    """CeciPipelineVariant response model."""

    col_names_for_table: ClassVar[list[str]] = ["id_", "name", "version"]


class CeciPipelineInstanceMixin:
    """Mixin for a Graph that is a CECI pipeline execution instance."""

    graph_template_id: int | None = None
    run_date: date = Field(..., description="Execution date")
    ceci_pipeline_variant_id: int = Field(..., description="Foreign key into CeciPipelineVariant table")


class CeciPipelineInstanceCreate(GraphCreate, CeciPipelineInstanceMixin):
    """Fields used to create a CeciPipelineInstance."""


class CeciPipelineInstance(Graph, CeciPipelineInstanceMixin):
    """CeciPipelineInstance response model."""

    col_names_for_table: ClassVar[list[str]] = ["uid_", "status", "run_date", "ceci_pipeline_variant_id"]
