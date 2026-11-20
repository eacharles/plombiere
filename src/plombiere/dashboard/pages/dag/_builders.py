"""Utilities for building Cytoscape graph elements from plombiere entities."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

# ---------------------------------------------------------------------------
# Shared Cytoscape stylesheet
# ---------------------------------------------------------------------------

STYLESHEET: list[dict[str, Any]] = [
    {
        "selector": "node",
        "style": {
            "label": "data(label)",
            "text-wrap": "wrap",
            "text-max-width": "130px",
            "font-size": "11px",
            "text-valign": "center",
            "text-halign": "center",
            "border-width": 1,
            "border-color": "#ccc",
        },
    },
    {
        "selector": ".stage",
        "style": {
            "shape": "roundrectangle",
            "background-color": "#4e79a7",
            "color": "white",
            "width": "160px",
            "height": "55px",
        },
    },
    {
        "selector": ".stage-override",
        "style": {
            "shape": "roundrectangle",
            "background-color": "#f28e2b",
            "color": "white",
            "width": "160px",
            "height": "55px",
        },
    },
    {
        "selector": ".stage-success",
        "style": {"background-color": "#59a14f"},
    },
    {
        "selector": ".stage-failure",
        "style": {"background-color": "#e15759"},
    },
    {
        "selector": ".stage-pending",
        "style": {"background-color": "#76b7b2"},
    },
    {
        "selector": ".file",
        "style": {
            "shape": "ellipse",
            "background-color": "#9c755f",
            "color": "white",
            "width": "130px",
            "height": "42px",
            "font-size": "10px",
        },
    },
    {
        "selector": "edge",
        "style": {
            "curve-style": "bezier",
            "target-arrow-shape": "triangle",
            "target-arrow-color": "#888",
            "line-color": "#aaa",
            "label": "data(label)",
            "font-size": "9px",
            "color": "#555",
            "text-background-color": "white",
            "text-background-opacity": 0.85,
            "text-background-padding": "2px",
            "width": 2,
        },
    },
]

DAG_LAYOUT: dict[str, Any] = {
    "name": "dagre",
    "rankDir": "TB",
    "nodeSep": 40,
    "rankSep": 70,
    "padding": 30,
}


# ---------------------------------------------------------------------------
# Pipeline / variant graph (from DB template records for a CeciPipeline)
# ---------------------------------------------------------------------------


def template_elements(
    pipeline_id: int,
    overrides: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build Cytoscape elements from a pipeline's template graph.

    Fetches AssocTemplate membership, then resolves each member to either a
    CeciStage (rectangle) or a CeciFileType (ellipse).  EdgeTemplate rows
    supply the directed edges with optional ``arg_name`` labels.

    ``overrides`` maps stage name → config dict; matching stages are styled
    as ``stage-override`` (orange) instead of the default blue.
    """
    from tisserande.local_sync import assoc_template as assoc_ops
    from tisserande.local_sync import edge_template as et_ops

    from plombiere.local_sync.node_types import ceci_file_type as file_type_ops
    from plombiere.local_sync.node_types import ceci_stage as stage_ops

    _BIG = 10_000  # bypass macon's default_pagination_limit=100

    member_ids: set[int] = {
        a.node_template_id
        for a in assoc_ops.get_rows(limit=_BIG)
        if a.graph_template_id == pipeline_id
    }
    if not member_ids:
        return []

    stages = {s.id_: s for s in stage_ops.get_rows(limit=_BIG) if s.id_ in member_ids}
    file_types = {f.id_: f for f in file_type_ops.get_rows(limit=_BIG) if f.id_ in member_ids}
    all_ids = set(stages) | set(file_types)

    elements: list[dict[str, Any]] = []

    for sid, stage in stages.items():
        has_override = bool(overrides and stage.name in overrides)
        elements.append({
            "data": {
                "id": str(sid),
                "label": stage.name or f"stage:{sid}",
                "node_type": "ceci_stage",
                "node_template_id": sid,
                "name": stage.name,
                "python_path": stage.python_path,
                "version": stage.version,
                "description": stage.description,
                "overrides": overrides.get(stage.name) if overrides else None,
            },
            "classes": "stage-override" if has_override else "stage",
        })

    for fid, ft in file_types.items():
        elements.append({
            "data": {
                "id": str(fid),
                "label": ft.name or f"file:{fid}",
                "node_type": "ceci_file_type",
                "node_template_id": fid,
                "name": ft.name,
                "file_format": ft.file_format,
                "version": ft.version,
                "description": ft.description,
            },
            "classes": "file",
        })

    for et in et_ops.get_rows(limit=_BIG):
        if et.from_id in all_ids and et.to_id in all_ids:
            elements.append({
                "data": {
                    "id": f"e{et.id_}",
                    "source": str(et.from_id),
                    "target": str(et.to_id),
                    "label": et.arg_name or "",
                }
            })

    return elements


# ---------------------------------------------------------------------------
# Instance graph (from DB execution records)
# ---------------------------------------------------------------------------

def instance_elements(pipeline_instance_id: UUID | str) -> list[dict[str, Any]]:
    """Build Cytoscape elements from a pipeline instance's stage nodes.

    Stage nodes are coloured by their embedded execution status. File nodes are
    shown as ellipses labelled by file basename.
    """
    from tisserande.local_sync import edge as edge_ops

    from plombiere.backend import BackendProvider

    _BIG = 10_000  # bypass macon's default_pagination_limit=100

    provider = BackendProvider.get()
    instance_id_str = str(pipeline_instance_id)

    associated_node_ids = {
        str(a.node_id)
        for a in provider.get_ops("association").get_rows(limit=_BIG)
        if str(a.graph_id) == instance_id_str
    }
    stage_nodes = [
        n for n in provider.get_ops("ceci_stage_call").get_rows(limit=_BIG)
        if str(n.uid_) in associated_node_ids
    ]

    all_edges = edge_ops.get_rows(limit=_BIG)
    file_nodes = [
        n for n in provider.get_ops("ceci_file").get_rows(limit=_BIG)
        if str(n.uid_) in associated_node_ids
    ]

    node_ids: set[str] = set()
    elements: list[dict[str, Any]] = []

    for n in stage_nodes:
        nid = str(n.uid_)
        node_ids.add(nid)
        raw_status = n.status
        status_str = (
            raw_status.value if hasattr(raw_status, "value") else str(raw_status or "pending")
        ).lower()
        elements.append({
            "data": {
                "id": nid,
                "label": n.name or "stage",
                "node_type": "ceci_stage_call",
                "name": n.name,
                "execution_id": str(n.execution_id) if n.execution_id else None,
                "status": status_str,
            },
            "classes": f"stage stage-{status_str}",
        })

    for n in file_nodes:
        nid = str(n.uid_)
        node_ids.add(nid)
        if n.file_path:
            label = Path(n.file_path).name
        else:
            label = nid[:8]
        elements.append({
            "data": {
                "id": nid,
                "label": label,
                "node_type": "ceci_file",
                "path": n.path,
                "arg_name": n.arg_name,
                "execution_id": str(n.execution_id) if n.execution_id else None,
            },
            "classes": "file",
        })

    for e in all_edges:
        src, dst = str(e.from_id), str(e.to_id)
        if src in node_ids and dst in node_ids:
            elements.append({
                "data": {"id": str(e.id_), "source": src, "target": dst, "label": ""}
            })

    return elements
