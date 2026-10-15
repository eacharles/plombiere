"""Pydantic models for CECI-specific provenance graph nodes."""

from typing import ClassVar, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .types import CeciNodeType


class _TypedNodeCreateMixin(BaseModel):
    arg_name: str | None = None
    execution_id: UUID | None = None


class _TypedNodeResponseMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_: UUID
    execution_id: UUID | None = None
    arg_name: str | None = None


class CeciFileNodeBase(BaseModel):
    """Model for a CECI file node.

    Schema nodes (execution_id=None) represent file type definitions.
    Instance nodes (execution_id set) represent specific files consumed or produced by a stage run.
    """

    type_: Literal["ceci_file"] = "ceci_file"
    path: str | None = Field(default=None, description="File path (instance nodes) or None (schema nodes)")
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
        "id_",
        "type_",
        "path",
        "data_registry_id",
        "ceci_file_schema_node_id",
    ]


class CeciStageNodeBase(BaseModel):
    """Model for a CECI stage node.

    Schema nodes (execution_id=None) represent stage class definitions.
    Instance nodes (execution_id set) represent specific stage executions.
    """

    type_: Literal["ceci_stage"] = "ceci_stage"
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


class CeciStageNodeCreate(CeciStageNodeBase, _TypedNodeCreateMixin):
    """Fields used to create a CeciStageNode."""


class CeciStageNode(CeciStageNodeBase, _TypedNodeResponseMixin):
    """CeciStageNode response model."""

    col_names_for_table: ClassVar[list[str]] = [
        "id_",
        "type_",
        "name",
        "python_path",
        "version",
        "ceci_stage_schema_node_id",
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
