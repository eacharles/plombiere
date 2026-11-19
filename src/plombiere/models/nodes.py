"""Pydantic models for CECI-specific provenance graph nodes."""

from datetime import datetime
from typing import ClassVar, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from tisserande.models.types import ExecutionStatus

from .types import CeciNodeType


class _TypedNodeCreateMixin(BaseModel):
    pass


class _TypedNodeResponseMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid_: UUID


class CeciFileNodeBase(BaseModel):
    """Model for a CECI file node.

    Schema nodes (ceci_pipeline_instance_id=None) represent file type definitions.
    Instance nodes (ceci_pipeline_instance_id set) represent specific files consumed or
    produced by a stage run.
    """

    node_type: Literal["ceci_file"] = "ceci_file"
    file_path: str | None = Field(
        default=None, description="File path (instance nodes) or None (schema nodes)"
    )
    creator: str = Field(default="ceci", description="Identifier of who or what created this data")
    description: str | None = Field(default=None, description="Description of the file type (schema nodes)")
    data_registry_id: int | None = Field(
        default=None, description="External data registry ID (instance nodes)"
    )
    ceci_file_schema_node_id: UUID | None = Field(
        default=None, description="Schema node this instance was created from"
    )


class CeciFileNodeCreate(CeciFileNodeBase, _TypedNodeCreateMixin):
    """Fields used to create a CeciFileNode."""


class CeciFileNode(CeciFileNodeBase, _TypedNodeResponseMixin):
    """CeciFileNode response model."""

    col_names_for_table: ClassVar[list[str]] = [
        "uid_",
        "node_type",
        "file_path",
        "data_registry_id",
        "ceci_file_schema_node_id",
    ]


class CeciStageNodeBase(BaseModel):
    """Model for a CECI stage node.

    Schema nodes (ceci_stage_schema_node_id=None) represent stage class definitions.
    Instance nodes (ceci_stage_schema_node_id set) represent specific stage executions.
    """

    node_type: Literal["ceci_stage"] = "ceci_stage"
    name: str | None = Field(default=None, description="Stage name (schema nodes)")
    python_path: str | None = Field(default=None, description="Python path to the stage class (schema nodes)")
    version: str | None = Field(default=None, description="Stage version string (schema nodes)")
    config: dict | None = Field(default=None, description="Default stage config (schema nodes)")
    overrides: dict | None = Field(default=None, description="Per-run config overrides (instance nodes)")
    data_registry_id: int | None = Field(
        default=None, description="External data registry ID (instance nodes)"
    )
    ceci_stage_schema_node_id: UUID | None = Field(
        default=None, description="Schema node this instance was created from"
    )
    ceci_pipeline_instance_id: UUID | None = Field(
        default=None, description="Pipeline instance this stage node belongs to"
    )
    status: ExecutionStatus | None = Field(default=None, description="Execution status of this stage")
    start_time: datetime | None = Field(default=None, description="When this stage started")
    end_time: datetime | None = Field(default=None, description="When this stage ended")
    duration_seconds: float | None = Field(default=None, description="Wall-clock duration in seconds")


class CeciStageNodeCreate(CeciStageNodeBase, _TypedNodeCreateMixin):
    """Fields used to create a CeciStageNode."""


class CeciStageNode(CeciStageNodeBase, _TypedNodeResponseMixin):
    """CeciStageNode response model."""

    col_names_for_table: ClassVar[list[str]] = [
        "uid_",
        "node_type",
        "name",
        "python_path",
        "version",
        "ceci_stage_schema_node_id",
        "status",
    ]


__all__ = [
    "CeciNodeType",
    "CeciFileNodeBase",
    "CeciFileNodeCreate",
    "CeciFileNode",
    "CeciStageNodeBase",
    "CeciStageNodeCreate",
    "CeciStageNode",
]
