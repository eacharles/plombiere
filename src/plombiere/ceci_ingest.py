"""Utilities for registering CECI pipeline definitions and stage executions.

Two main entry points:

``register_pipeline_from_yaml``
    Reads a CECI pipeline YAML and populates schema-level (execution_id=None)
    CeciStageNode records — one per unique stage class.

``ingest_stage_logs``
    Reads a directory of ``{stage_name}.out`` log files produced by a CECI
    pipeline run and creates one Execution + one instance CeciStageNode per
    file, plus CeciFileNode instances and edges for every file handle logged.

Usage::

    from plombiere.ceci_ingest import register_pipeline_from_yaml, ingest_stage_logs
    from tisserande.db.base import init_db

    init_db("sqlite+aiosqlite:///my.db")
    _, schema_nodes = register_pipeline_from_yaml("pz_dp1_6band.yaml")
    pipeline_exec, results = ingest_stage_logs("logs/", schema_nodes=schema_nodes)
    print(pipeline_exec.status, pipeline_exec.duration_seconds)
    for exec_, stage_node, file_nodes in results:
        print(exec_.status, stage_node.name, len(file_nodes))
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import yaml

from tisserande.local_sync import edge as edge_ops
from tisserande.local_sync import execution as execution_ops
from tisserande.local_sync import node as node_ops
from tisserande.models.edges import EdgeCreate
from tisserande.models.execution import Execution, ExecutionCreate
from tisserande.models.types import ExecutionStatus

from .models.ceci_pipelines import CeciPipelineCreate
from .models.nodes import CeciFileNode, CeciFileNodeCreate, CeciStageNode, CeciStageNodeCreate

_EXECUTING_RE = re.compile(
    r"Executing stage:\s+(?P<classname>\S+)\s+@\s+(?P<ts>.+)"
)
_COMPLETE_RE = re.compile(
    r"Stage complete:\s+(?P<classname>\S+)\s+@\s+(?P<ts>.+?)\s+took\s+(?P<minutes>[\d.]+)\s+minutes"
)
_FAILED_RE = re.compile(
    r"Stage failed:\s+(?P<classname>\S+)\s+@\s+(?P<ts>.+?)\s+after\s+(?P<minutes>[\d.]+)\s+minutes"
)
# "Inserting handle into data store.  {tag}: {path}, {stage_name}"
_HANDLE_RE = re.compile(
    r"Inserting handle into data store\.\s+(?P<tag>\S+):\s+(?P<path>\S+),\s+\S+"
)
_TS_FMT = "%Y-%m-%d %H:%M:%S.%f"


@dataclass
class FileHandleRecord:
    """A single file handle parsed from a log line."""

    tag: str
    path: str
    is_output: bool


@dataclass
class StageLogRecord:
    """Parsed data extracted from a single stage log file."""

    instance_name: str
    classname: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    status: ExecutionStatus
    log_path: Path
    file_handles: list[FileHandleRecord] = field(default_factory=list)


def _resolve_handle(tag: str, raw_path: str) -> FileHandleRecord:
    """Determine if a handle is an input or output and clean its path."""
    p = Path(raw_path)
    if p.name.startswith("inprogress_"):
        final_path = str(p.parent / p.name[len("inprogress_"):])
        return FileHandleRecord(tag=tag, path=final_path, is_output=True)
    return FileHandleRecord(tag=tag, path=raw_path, is_output=False)


def _parse_stage_classes(stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate stages by python_path, keeping the first occurrence."""
    seen: dict[str, bool] = {}
    unique: list[dict[str, Any]] = []
    for stage in stages:
        python_path = f"{stage['module_name']}.{stage['classname']}"
        if python_path not in seen:
            seen[python_path] = True
            unique.append({"name": stage["classname"], "python_path": python_path})
    return unique


def register_pipeline_from_yaml(
    yaml_path: str | Path,
    *,
    name: str | None = None,
    description: str = "",
    config: dict | None = None,
) -> tuple[CeciPipelineCreate, list[CeciStageNode]]:
    """Parse a CECI pipeline YAML and register schema-level records in the database.

    Parameters
    ----------
    yaml_path:
        Path to the pipeline YAML file (e.g. ``pz_dp1_6band.yaml``).
    name:
        Pipeline name. Defaults to the YAML file stem (e.g. ``pz_dp1_6band``).
    description:
        Human-readable description stored in the pipeline record.
    config:
        Default pipeline config dict.

    Returns
    -------
    pipeline_create:
        A ``CeciPipelineCreate`` model populated from the YAML.
    stage_nodes:
        List of ``CeciStageNode`` response models, one per unique stage class.
    """
    yaml_path = Path(yaml_path)
    pipeline_name = name or yaml_path.stem

    with yaml_path.open() as f:
        structure: dict[str, Any] = yaml.safe_load(f)

    stages_raw: list[dict[str, Any]] = structure.get("stages", [])
    if not stages_raw:
        raise ValueError(f"No stages found in {yaml_path}")

    unique_stage_classes = _parse_stage_classes(stages_raw)

    stage_nodes: list[CeciStageNode] = []
    for stage_class in unique_stage_classes:
        create_kwargs = CeciStageNodeCreate(
            name=stage_class["name"],
            python_path=stage_class["python_path"],
        ).model_dump()
        row = node_ops.create_row(**create_kwargs)
        stage_nodes.append(CeciStageNode.model_validate(row))

    pipeline_create = CeciPipelineCreate(
        name=pipeline_name,
        description=description,
        structure=structure,
        config=config or {},
    )

    return pipeline_create, stage_nodes


def stage_node_ids(stage_nodes: list[CeciStageNode]) -> list[UUID]:
    """Extract IDs from a list of stage nodes (convenience for building assoc records)."""
    return [n.id_ for n in stage_nodes]


# ---------------------------------------------------------------------------
# Log parsing
# ---------------------------------------------------------------------------


def _parse_log_file(log_path: Path) -> StageLogRecord | None:
    """Parse a single stage .out file.

    Returns None if the file has no recognisable start or end markers.
    """
    instance_name = log_path.stem
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_seconds: float | None = None
    status: ExecutionStatus | None = None
    classname: str | None = None
    file_handles: list[FileHandleRecord] = []

    with log_path.open(errors="replace") as f:
        for line in f:
            line = line.rstrip()

            if m := _EXECUTING_RE.match(line):
                classname = m.group("classname")
                start_time = datetime.strptime(m.group("ts").strip(), _TS_FMT)

            elif m := _COMPLETE_RE.match(line):
                end_time = datetime.strptime(m.group("ts").strip(), _TS_FMT)
                duration_seconds = float(m.group("minutes")) * 60.0
                status = ExecutionStatus.SUCCESS

            elif m := _FAILED_RE.match(line):
                end_time = datetime.strptime(m.group("ts").strip(), _TS_FMT)
                duration_seconds = float(m.group("minutes")) * 60.0
                status = ExecutionStatus.FAILURE

            elif m := _HANDLE_RE.match(line):
                file_handles.append(_resolve_handle(m.group("tag"), m.group("path")))

    if start_time is None or status is None or classname is None:
        return None

    if end_time is None:
        end_time = start_time

    return StageLogRecord(
        instance_name=instance_name,
        classname=classname,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration_seconds or 0.0,
        status=status,
        log_path=log_path,
        file_handles=file_handles,
    )


def ingest_stage_logs(
    log_dir: str | Path,
    *,
    schema_nodes: list[CeciStageNode] | None = None,
) -> tuple[Execution, list[tuple[Execution, CeciStageNode, list[CeciFileNode]]]]:
    """Read a directory of CECI stage log files and write execution records.

    Creates one pipeline-level ``Execution`` and for each ``{stage_name}.out``
    file creates a stage ``Execution``, a ``CeciStageNode`` instance, one
    ``CeciFileNode`` per logged file handle, and connecting ``Edge`` records.

    Parameters
    ----------
    log_dir:
        Directory containing ``*.out`` log files.
    schema_nodes:
        Schema-level ``CeciStageNode`` records to link against. Optional.

    Returns
    -------
    ``(pipeline_execution, stage_results)`` where ``stage_results`` is a list
    of ``(Execution, CeciStageNode, list[CeciFileNode])`` triples.
    """
    log_dir = Path(log_dir)
    schema_by_classname: dict[str, CeciStageNode] = {}
    if schema_nodes:
        for sn in schema_nodes:
            if sn.name and sn.name not in schema_by_classname:
                schema_by_classname[sn.name] = sn

    records: list[StageLogRecord] = []
    for log_path in sorted(log_dir.glob("*.out")):
        record = _parse_log_file(log_path)
        if record is not None:
            records.append(record)

    if not records:
        raise ValueError(f"No parseable stage log files found in {log_dir}")

    pipeline_start = min(r.start_time for r in records)
    pipeline_end = max(r.end_time for r in records)
    pipeline_duration = (pipeline_end - pipeline_start).total_seconds()
    any_failed = any(r.status == ExecutionStatus.FAILURE for r in records)
    pipeline_status = ExecutionStatus.FAILURE if any_failed else ExecutionStatus.SUCCESS

    pipeline_exec_row = execution_ops.create_row(
        **ExecutionCreate(
            status=pipeline_status,
            start_time=pipeline_start,
            end_time=pipeline_end,
            duration_seconds=pipeline_duration,
        ).model_dump()
    )
    pipeline_execution_id: UUID = pipeline_exec_row.id_

    stage_results: list[tuple[Execution, CeciStageNode, list[CeciFileNode]]] = []

    for record in records:
        exec_row = execution_ops.create_row(
            **ExecutionCreate(
                status=record.status,
                start_time=record.start_time,
                end_time=record.end_time,
                duration_seconds=record.duration_seconds,
                parent_execution_id=pipeline_execution_id,
            ).model_dump()
        )

        schema_node = schema_by_classname.get(record.classname)
        stage_row = node_ops.create_row(
            **CeciStageNodeCreate(
                name=record.instance_name,
                execution_id=exec_row.id_,
                ceci_stage_schema_node_id=schema_node.id_ if schema_node else None,
            ).model_dump()
        )

        execution_ops.update_row(exec_row.id_, function_node_id=stage_row.id_)

        file_nodes: list[CeciFileNode] = []
        for handle in record.file_handles:
            file_row = node_ops.create_row(
                **CeciFileNodeCreate(
                    path=handle.path,
                    arg_name=handle.tag,
                    execution_id=exec_row.id_,
                ).model_dump()
            )
            file_node = CeciFileNode.model_validate(file_row)
            file_nodes.append(file_node)

            if handle.is_output:
                edge_ops.create_row(
                    **EdgeCreate(
                        from_id=stage_row.id_,
                        to_id=file_row.id_,
                        execution_id=exec_row.id_,
                    ).model_dump()
                )
            else:
                edge_ops.create_row(
                    **EdgeCreate(
                        from_id=file_row.id_,
                        to_id=stage_row.id_,
                        execution_id=exec_row.id_,
                    ).model_dump()
                )

        exec_response = Execution.model_validate(exec_row)
        stage_response = CeciStageNode.model_validate(stage_row)
        stage_results.append((exec_response, stage_response, file_nodes))

    return Execution.model_validate(pipeline_exec_row), stage_results
