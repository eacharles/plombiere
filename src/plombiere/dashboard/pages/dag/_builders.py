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
    "rankDir": "LR",
    "nodeSep": 25,
    "rankSep": 90,
    "padding": 30,
}


# ---------------------------------------------------------------------------
# Pipeline / variant graph (from YAML structure)
# ---------------------------------------------------------------------------

def pipeline_elements(
    structure: dict[str, Any],
    overrides: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build bipartite Cytoscape elements from a pipeline YAML structure.

    Creates stage nodes (rectangles) and file-handle nodes (ellipses) as
    intermediate vertices. A handle shared between two stages produces:
      producer_stage → file_handle_node → consumer_stage
    """
    stages: list[dict[str, Any]] = structure.get("stages", [])
    if not stages:
        return []

    # Track the first stage (by YAML index) that introduces each handle value.
    handle_first: dict[str, tuple[int, str]] = {}
    for i, stage in enumerate(stages):
        for handle in stage.get("aliases", {}).values():
            if handle not in handle_first:
                handle_first[handle] = (i, stage["name"])

    elements: list[dict[str, Any]] = []

    # Stage nodes
    for stage in stages:
        name = stage["name"]
        classname = stage.get("classname", name)
        has_override = bool(overrides and name in overrides)
        elements.append({
            "data": {"id": name, "label": f"{classname}\n({name})"},
            "classes": "stage-override" if has_override else "stage",
        })

    # File-handle nodes and bipartite edges
    seen_file_nodes: set[str] = set()
    seen_edges: set[tuple[str, str]] = set()

    for i, stage in enumerate(stages):
        dst = stage["name"]
        for handle in stage.get("aliases", {}).values():
            first_i, src = handle_first[handle]
            if first_i >= i:
                continue
            file_id = f"__file__{handle}"
            if file_id not in seen_file_nodes:
                seen_file_nodes.add(file_id)
                elements.append({
                    "data": {"id": file_id, "label": handle},
                    "classes": "file",
                })
            for edge in ((src, file_id), (file_id, dst)):
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    elements.append({
                        "data": {"id": f"{edge[0]}--{edge[1]}", "source": edge[0], "target": edge[1], "label": ""}
                    })

    return elements


# ---------------------------------------------------------------------------
# Instance graph (from DB execution records)
# ---------------------------------------------------------------------------

def instance_elements(execution_id: UUID | str) -> list[dict[str, Any]]:
    """Build Cytoscape elements from a pipeline instance's execution records.

    Stage nodes are coloured by per-stage execution status. File nodes are
    shown as ellipses labelled by arg_name or file basename.
    """
    from tisserande.local_sync import edge as edge_ops
    from tisserande.local_sync import execution as exec_ops

    from plombiere.backend import BackendProvider

    provider = BackendProvider.get()
    exec_id_str = str(execution_id)

    all_execs = exec_ops.get_rows()
    exec_status_map: dict[str, Any] = {str(e.id_): e.status for e in all_execs}
    stage_exec_ids: set[str] = {
        str(e.id_)
        for e in all_execs
        if e.parent_execution_id and str(e.parent_execution_id) == exec_id_str
    }

    stage_nodes = [
        n for n in provider.get_ops("ceci_stage_node").get_rows()
        if n.execution_id and str(n.execution_id) in stage_exec_ids
    ]
    file_nodes = [
        n for n in provider.get_ops("ceci_file_node").get_rows()
        if n.execution_id and str(n.execution_id) in stage_exec_ids
    ]

    node_ids: set[str] = set()
    elements: list[dict[str, Any]] = []

    for n in stage_nodes:
        nid = str(n.id_)
        node_ids.add(nid)
        raw_status = exec_status_map.get(str(n.execution_id))
        status_str = (
            raw_status.value if hasattr(raw_status, "value") else str(raw_status)
        ).lower()
        elements.append({
            "data": {"id": nid, "label": n.name or "stage"},
            "classes": f"stage stage-{status_str}",
        })

    for n in file_nodes:
        nid = str(n.id_)
        node_ids.add(nid)
        if n.arg_name:
            label = n.arg_name
        elif n.path:
            label = Path(n.path).name
        else:
            label = nid[:8]
        elements.append({
            "data": {"id": nid, "label": label},
            "classes": "file",
        })

    for e in edge_ops.get_rows():
        src, dst = str(e.from_id), str(e.to_id)
        if src in node_ids and dst in node_ids:
            elements.append({
                "data": {"id": str(e.id_), "source": src, "target": dst, "label": ""}
            })

    return elements
