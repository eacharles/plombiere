"""Pipeline DAG page — shows stage topology from the pipeline YAML structure."""

import dash
import dash_cytoscape as cyto
from dash import Input, Output, State, callback, clientside_callback, dcc, html

from plombiere.backend import BackendProvider
from plombiere.dashboard.pages.dag._builders import DAG_LAYOUT, STYLESHEET, pipeline_elements

dash.register_page(__name__, path="/dag/pipeline", name="Pipeline DAG")

_DETAIL_PANEL_STYLE = {
    "width": "280px",
    "flexShrink": "0",
    "borderLeft": "1px solid #dee2e6",
    "padding": "12px",
    "backgroundColor": "#f8f9fa",
    "overflowY": "auto",
    "marginTop": "16px",
    "maxHeight": "620px",
    "fontSize": "13px",
}

_PLACEHOLDER = html.P(
    "Right-click a node to see its details.",
    style={"color": "#aaa", "fontStyle": "italic"},
)


def _kv_row(key, value):
    return html.Div(
        [
            html.Span(key, style={"fontWeight": "600", "color": "#555", "display": "block", "marginBottom": "2px"}),
            html.Span(
                str(value) if value is not None else "—",
                style={"wordBreak": "break-all", "color": "#333"},
            ),
        ],
        style={"padding": "6px 0", "borderBottom": "1px solid #eee"},
    )


def layout(**kwargs):
    try:
        ops = BackendProvider.get().get_ops("ceci_pipeline")
        options = [{"label": p.name, "value": p.id_} for p in ops.get_rows()]
    except Exception:
        options = []

    preselect = None
    if "id" in kwargs:
        try:
            preselect = int(kwargs["id"])
        except (ValueError, TypeError):
            pass

    return html.Div([
        html.H2("Pipeline DAG"),
        html.P(
            "Right-click a node to see its details.",
            style={"color": "#888", "fontSize": "13px"},
        ),
        html.Hr(),
        dcc.Dropdown(
            id="dag-pipeline-select",
            options=options,
            value=preselect,
            placeholder="Select a pipeline…",
            style={"maxWidth": "500px"},
        ),
        html.Div(
            [
                html.Div(id="dag-pipeline-graph-container", style={"flex": "1 1 0%", "minWidth": 0, "marginTop": "16px"}),
                html.Div(id="dag-pipeline-detail-panel", children=_PLACEHOLDER, style=_DETAIL_PANEL_STYLE),
            ],
            style={"display": "flex", "gap": "0", "alignItems": "flex-start"},
        ),
        dcc.Store(id="dag-pipeline-hovered-node"),
        dcc.Store(id="dag-pipeline-rightclick-node"),
        html.Button(id="dag-pipeline-rightclick-trigger", n_clicks=0, style={"display": "none"}),
    ])


@callback(
    Output("dag-pipeline-graph-container", "children"),
    Input("dag-pipeline-select", "value"),
)
def render_pipeline_dag(pipeline_id):
    if pipeline_id is None:
        return html.P("Select a pipeline above.", style={"color": "#888", "fontStyle": "italic"})
    try:
        ops = BackendProvider.get().get_ops("ceci_pipeline")
        pipeline = ops.get_row(pipeline_id)
        elements = pipeline_elements(pipeline.structure)
        if not elements:
            return html.P("No stages found in this pipeline.")
        return cyto.Cytoscape(
            id="dag-pipeline-graph",
            elements=elements,
            layout=DAG_LAYOUT,
            style={"width": "100%", "height": "620px", "border": "1px solid #dee2e6", "borderRadius": "4px"},
            stylesheet=STYLESHEET,
        )
    except Exception as e:
        return html.P(f"Error: {e}", style={"color": "red"})


clientside_callback(
    "function(d) { return d != null ? d : window.dash_clientside.no_update; }",
    Output("dag-pipeline-hovered-node", "data"),
    Input("dag-pipeline-graph", "mouseoverNodeData"),
    prevent_initial_call=True,
)

clientside_callback(
    "function(n, h) { if (n && h) return h; return window.dash_clientside.no_update; }",
    Output("dag-pipeline-rightclick-node", "data"),
    Input("dag-pipeline-rightclick-trigger", "n_clicks"),
    State("dag-pipeline-hovered-node", "data"),
    prevent_initial_call=True,
)


@callback(
    Output("dag-pipeline-detail-panel", "children"),
    Input("dag-pipeline-rightclick-node", "data"),
    prevent_initial_call=True,
)
def show_pipeline_node_detail(node_data):
    if not node_data:
        return _PLACEHOLDER
    node_type = node_data.get("node_type")
    if node_type == "stage":
        title = f"Stage: {node_data.get('stage_name', '?')}"
        aliases = node_data.get("aliases") or {}
        fields = [
            ("name", node_data.get("stage_name")),
            ("classname", node_data.get("classname")),
            ("aliases", ", ".join(f"{k}→{v}" for k, v in aliases.items()) or "—"),
        ]
    elif node_type == "file":
        title = f"File handle: {node_data.get('handle', '?')}"
        fields = [("handle", node_data.get("handle"))]
    else:
        return _PLACEHOLDER

    return html.Div([
        html.H6(title, style={"marginTop": 0, "marginBottom": "10px", "color": "#333"}),
        html.Div([_kv_row(k, v) for k, v in fields]),
    ])
