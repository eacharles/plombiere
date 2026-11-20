"""Build a CeciPipeline template graph from a DOT file.

Entry point
-----------
``register_pipeline_from_dot``
    Parses a DOT file and creates:

    * One ``CeciStage`` (ShellFunction template) per stage node.
    * One ``CeciFileType`` (DataFileType template) per file/data node.
    * One ``CeciPipeline`` (GraphTemplate) for the whole pipeline.
    * One ``AssocTemplate`` per node linking it to the pipeline.
    * One ``EdgeTemplate`` per directed edge, carrying the optional ``arg_name``
      from the DOT edge's ``label`` or ``arg_name`` attribute.

Node classification
-------------------
Nodes must carry a ``type`` attribute set to one of:

* ``type=stage`` → ``CeciStage`` template.
* ``type=input`` or ``type=output`` → ``CeciFileType`` template.

Labels override node IDs as the recorded name.  Stage nodes may carry
``python_path`` and ``description`` attributes; file nodes may carry
``file_format`` and ``description``.

Usage::

    from plombiere.ceci_pipeline_dot import register_pipeline_from_dot
    from tisserande.db.base import init_db

    init_db("sqlite+aiosqlite:///my.db")
    pipeline, stages, file_types = register_pipeline_from_dot(
        "my_pipeline.dot", name="my_pipeline", version="1.0"
    )
"""

from __future__ import annotations

from pathlib import Path

try:
    import pydot
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "pydot is required for DOT file parsing: pip install pydot"
    ) from exc

from tisserande.local_sync import assoc_template as _assoc_template_ops
from tisserande.local_sync import edge_template as _edge_template_ops

from .local_sync import ceci_pipeline as _pipeline_ops
from .local_sync.node_types import ceci_file_type as _file_type_ops
from .local_sync.node_types import ceci_stage as _stage_ops
from .models import CeciPipeline
from .models.nodes import CeciFileType, CeciStage

_PSEUDO_NAMES: frozenset[str] = frozenset({"graph", "node", "edge", ""})


def _unquote(value: str) -> str:
    """Strip surrounding quotes that pydot adds to attribute string values."""
    return value.strip('"').strip("'")


def _attr(node: pydot.Node | pydot.Edge, key: str) -> str | None:
    """Return an unquoted attribute value, or None if absent."""
    raw = node.get_attributes().get(key)
    if raw is None:
        return None
    return _unquote(str(raw)) or None


def _is_stage(node: pydot.Node) -> bool:
    """Return True if the node's ``type`` attribute is ``stage``."""
    node_type = _attr(node, "type")
    if node_type is None:
        raise ValueError(
            f"Node '{_unquote(node.get_name())}' has no 'type' attribute. "
            "Set type=stage, type=input, or type=output."
        )
    return node_type.lower() == "stage"


def _node_label(node: pydot.Node) -> str:
    """Return the display label, falling back to the node ID."""
    label = _attr(node, "label")
    if label:
        return label
    return _unquote(node.get_name())


def _collect_nodes(graph: pydot.Dot) -> list[pydot.Node]:
    """Collect real nodes from the top-level graph and all subgraphs."""
    seen: set[str] = set()
    result: list[pydot.Node] = []

    def _add(node: pydot.Node) -> None:
        name = _unquote(node.get_name())
        if name in _PSEUDO_NAMES or name in seen:
            return
        seen.add(name)
        result.append(node)

    for n in graph.get_nodes():
        _add(n)
    for sg in graph.get_subgraphs():
        for n in sg.get_nodes():
            _add(n)
    return result


def _collect_edges(graph: pydot.Dot) -> list[pydot.Edge]:
    """Collect all edges from the top-level graph and all subgraphs."""
    result = list(graph.get_edges())
    for sg in graph.get_subgraphs():
        result.extend(sg.get_edges())
    return result


def register_pipeline_from_dot(
    dot_file: Path | str,
    name: str,
    version: str = "1.0",
    description: str | None = None,
) -> tuple[CeciPipeline, list[CeciStage], list[CeciFileType]]:
    """Parse *dot_file* and populate the full CeciPipeline template graph.

    Parameters
    ----------
    dot_file:
        Path to the ``.dot`` / ``.gv`` file describing the bipartite pipeline
        DAG (stage nodes ↔ file nodes).
    name:
        Name stored on the ``CeciPipeline`` record.
    version:
        Version string applied to the pipeline and to every node template
        created from it.
    description:
        Optional free-text description stored on the ``CeciPipeline`` record.

    Returns
    -------
    ``(pipeline, stages, file_types)`` where *pipeline* is the new
    ``CeciPipeline``, *stages* is the list of ``CeciStage`` templates, and
    *file_types* is the list of ``CeciFileType`` templates.
    """
    graphs = pydot.graph_from_dot_file(str(dot_file))
    if not graphs:
        raise ValueError(f"No graph found in {dot_file}")
    graph = graphs[0]

    nodes = _collect_nodes(graph)
    edges = _collect_edges(graph)

    # -- Create node templates ------------------------------------------
    stages: list[CeciStage] = []
    file_types: list[CeciFileType] = []
    # Maps the raw DOT node name → node_template.id_
    id_map: dict[str, int] = {}

    for node in nodes:
        node_name = _unquote(node.get_name())
        label = _node_label(node)

        if _is_stage(node):
            row = _stage_ops.create_row(
                name=label,
                version=version,
                python_path=_attr(node, "python_path"),
                description=_attr(node, "description"),
            )
            stage = CeciStage.model_validate(row)
            stages.append(stage)
            id_map[node_name] = stage.id_
        else:
            row = _file_type_ops.create_row(
                name=label,
                version=version,
                file_format=_attr(node, "file_format"),
                description=_attr(node, "description"),
            )
            file_type = CeciFileType.model_validate(row)
            file_types.append(file_type)
            id_map[node_name] = file_type.id_

    # -- Create the pipeline (GraphTemplate) ----------------------------
    pipeline_row = _pipeline_ops.create_row(
        name=name,
        version=version,
        description=description,
        structure={},
        config={},
    )
    pipeline = CeciPipeline.model_validate(pipeline_row)

    # -- AssocTemplate: every node template is a member of the pipeline -
    for node_template_id in id_map.values():
        _assoc_template_ops.create_row(
            node_template_id=node_template_id,
            graph_template_id=pipeline.id_,
        )

    # -- EdgeTemplate: directed edges from the DOT ----------------------
    for edge in edges:
        src = _unquote(str(edge.get_source()))
        dst = _unquote(str(edge.get_destination()))
        if src not in id_map or dst not in id_map:
            continue
        # Accept edge label or explicit arg_name attribute as the arg_name
        arg_name = _attr(edge, "label") or _attr(edge, "arg_name")
        _edge_template_ops.create_row(
            from_id=id_map[src],
            to_id=id_map[dst],
            arg_name=arg_name,
        )

    return pipeline, stages, file_types
