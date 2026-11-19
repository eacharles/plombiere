"""Pydantic models for CECI-specific provenance graph nodes."""

from typing import ClassVar, Literal

from pydantic import Field

from tisserande.models.function_types import (
    ShellFunction,
    ShellFunctionCall,
    ShellFunctionCallCreate,
    ShellFunctionCreate,
)
from tisserande.models.data_types import DataFile, DataFileCreate
from tisserande.models.data_types import DataFileType as _DataFileType
from tisserande.models.data_types import DataFileTypeCreate as _DataFileTypeCreate

from .types import CeciNodeType


class CeciFileMixin:
    """Mixin for a DataFile that is a CECI pipeline file instance."""

    description: str | None = Field(default=None, description="Description of this file")
    data_registry_id: int | None = Field(
        default=None, description="External data registry ID"
    )


class CeciFileCreate(DataFileCreate, CeciFileMixin):
    """Fields used to create a CeciFile."""

    node_type: Literal["ceci_file"] = "ceci_file"


class CeciFile(DataFile, CeciFileMixin):
    """CeciFile response model."""

    node_type: Literal["ceci_file"] = "ceci_file"
    col_names_for_table: ClassVar[list[str]] = [
        "uid_",
        "node_type",
        "file_path",
        "data_registry_id",
    ]


class CeciStageCallMixin:
    """Mixin for a ShellFunctionCall that is a CECI pipeline stage execution instance."""

    name: str | None = Field(default=None, description="Stage name")
    python_path: str | None = Field(default=None, description="Python path to the stage class")
    version: str | None = Field(default=None, description="Stage version string")
    config: dict | None = Field(default=None, description="Stage config")
    overrides: dict | None = Field(default=None, description="Per-run config overrides")
    data_registry_id: int | None = Field(default=None, description="External data registry ID")
    duration_seconds: float | None = Field(default=None, description="Wall-clock duration in seconds")


class CeciStageCallCreate(ShellFunctionCallCreate, CeciStageCallMixin):
    """Fields used to create a CeciStageCall."""

    node_type: Literal["ceci_stage_call"] = "ceci_stage_call"


class CeciStageCall(ShellFunctionCall, CeciStageCallMixin):
    """CeciStageCall response model."""

    node_type: Literal["ceci_stage_call"] = "ceci_stage_call"
    col_names_for_table: ClassVar[list[str]] = [
        "uid_",
        "node_type",
        "name",
        "python_path",
        "version",
        "status",
    ]


class CeciFileTypeMixin:
    """Mixin for a DataFileType template that describes a CECI pipeline file type."""

    node_template_type: Literal["ceci_file_type"] = "ceci_file_type"
    description: str | None = Field(default=None, description="Description of this CECI file type")


class CeciFileTypeCreate(_DataFileTypeCreate, CeciFileTypeMixin):
    """Fields used to create a CeciFileType template."""


class CeciFileType(_DataFileType, CeciFileTypeMixin):
    """CeciFileType response model."""

    col_names_for_table: ClassVar[list[str]] = [
        "id_",
        "name",
        "version",
        "description",
    ]


class CeciStageMixin:
    """Mixin for a ShellFunction template that describes a CECI pipeline stage type."""

    python_path: str | None = Field(default=None, description="Python dotted path to the stage class")
    description: str | None = Field(default=None, description="Description of this stage type")


class CeciStageCreate(ShellFunctionCreate, CeciStageMixin):
    """Fields used to create a CeciStage template."""

    node_template_type: Literal["ceci_stage"] = "ceci_stage"


class CeciStage(ShellFunction, CeciStageMixin):
    """CeciStage template response model."""

    node_template_type: Literal["ceci_stage"] = "ceci_stage"
    col_names_for_table: ClassVar[list[str]] = [
        "id_",
        "name",
        "python_path",
        "version",
    ]


__all__ = [
    "CeciNodeType",
    "CeciFileMixin",
    "CeciFileCreate",
    "CeciFile",
    "CeciStageCallMixin",
    "CeciStageCallCreate",
    "CeciStageCall",
    "CeciFileTypeMixin",
    "CeciFileTypeCreate",
    "CeciFileType",
    "CeciStageMixin",
    "CeciStageCreate",
    "CeciStage",
]
