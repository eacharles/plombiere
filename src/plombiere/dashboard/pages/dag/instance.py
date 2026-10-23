"""Instance DAG page — shows actual stage and file nodes from a pipeline run."""

import dash
import dash_cytoscape as cyto
from dash import Input, Output, State, callback, clientside_callback, dcc, html

from plombiere.backend import BackendProvider
from plombiere.dashboard.pages.dag._builders import DAG_LAYOUT, STYLESHEET, instance_elements

dash.register_page(__name__, path="/dag/instance", name="Instance DAG")

_STATUS_LEGEND = html.Div(
    [
        html.Span("■ success", style={"color": "#59a14f", "marginRight": "16px", "fontWeight": "bold"}),
        html.Span("■ failure", style={"color": "#e15759", "marginRight": "16px", "fontWeight": "bold"}),
        html.Span("■ pending/other", style={"color": "#76b7b2", "marginRight": "16px", "fontWeight": "bold"}),
        html.Span("● file node", style={"color": "#9c755f", "fontWeight": "bold"}),
    ],
    style={"fontSize": "12px", "marginBottom": "10px"},
)

_DETAIL_PANEL_STYLE = {
    "width": "280px",
    "flexShrink": "0",
    "borderLeft": "1px solid #dee2e6",
    "padding": "12px",
    "backgroundColor": "#f8f9fa",
    "overflowY": "auto",
    "marginTop": "16px",
    "maxHeight": "680px",
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
        provider = BackendProvider.get()
        instances = provider.get_ops("ceci_pipeline_instance").get_rows()
        variants = {v.id_: v.name for v in provider.get_ops("ceci_pipeline_variant").get_rows()}
        options = [
            {
                "label": f"{i.run_date} — {str(i.status.value if hasattr(i.status, 'value') else i.status)}  ({variants.get(i.ceci_pipeline_variant_id, '')})",
                "value": str(i.id_),
            }
            for i in instances
        ]
    except Exception:
        options = []

    preselect = kwargs.get("id")

    return html.Div([
        html.H2("Instance DAG"),
        html.P(
            "Stage nodes are coloured by execution status. Right-click any node for details.",
            style={"color": "#888", "fontSize": "13px"},
        ),
        html.Hr(),
        dcc.Dropdown(
            id="dag-instance-select",
            options=options,
            value=preselect,
            placeholder="Select a pipeline instance…",
            style={"maxWidth": "700px"},
        ),
        html.Div(
            [
                html.Div(id="dag-instance-graph-container", style={"flex": "1 1 0%", "minWidth": 0, "marginTop": "16px"}),
                html.Div(id="dag-instance-detail-panel", children=_PLACEHOLDER, style=_DETAIL_PANEL_STYLE),
            ],
            style={"display": "flex", "gap": "0", "alignItems": "flex-start"},
        ),
        dcc.Store(id="dag-instance-hovered-node"),
        dcc.Store(id="dag-instance-rightclick-node"),
        html.Button(id="dag-instance-rightclick-trigger", n_clicks=0, style={"display": "none"}),
    ])


@callback(
    Output("dag-instance-graph-container", "children"),
    Input("dag-instance-select", "value"),
)
def render_instance_dag(instance_id_str):
    if instance_id_str is None:
        return html.P("Select an instance above.", style={"color": "#888", "fontStyle": "italic"})
    try:
        from uuid import UUID

        provider = BackendProvider.get()
        instance = provider.get_ops("ceci_pipeline_instance").get_row(UUID(instance_id_str))
        if instance.execution_id is None:
            return html.P(
                "This instance has no linked execution record — it was ingested before execution tracking was added.",
                style={"color": "#888"},
            )
        elements = instance_elements(instance.execution_id)
        if not elements:
            return html.P("No nodes found for this instance.")
        return html.Div([
            _STATUS_LEGEND,
            cyto.Cytoscape(
                id="dag-instance-graph",
                elements=elements,
                layout=DAG_LAYOUT,
                style={"width": "100%", "height": "680px", "border": "1px solid #dee2e6", "borderRadius": "4px"},
                stylesheet=STYLESHEET,
            ),
        ])
    except Exception as e:
        return html.P(f"Error: {e}", style={"color": "red"})


clientside_callback(
    "function(d) { return d != null ? d : window.dash_clientside.no_update; }",
    Output("dag-instance-hovered-node", "data"),
    Input("dag-instance-graph", "mouseoverNodeData"),
    prevent_initial_call=True,
)

clientside_callback(
    "function(n, h) { if (n && h) return h; return window.dash_clientside.no_update; }",
    Output("dag-instance-rightclick-node", "data"),
    Input("dag-instance-rightclick-trigger", "n_clicks"),
    State("dag-instance-hovered-node", "data"),
    prevent_initial_call=True,
)


@callback(
    Output("dag-instance-detail-panel", "children"),
    Input("dag-instance-rightclick-node", "data"),
    prevent_initial_call=True,
)
def show_instance_node_detail(node_data):
    if not node_data:
        return _PLACEHOLDER
    node_type = node_data.get("node_type")
    node_id_str = node_data.get("id")
    try:
        from uuid import UUID
        provider = BackendProvider.get()
        if node_type == "ceci_stage":
            row = provider.get_ops("ceci_stage_node").get_row(UUID(node_id_str))
            title = f"Stage: {row.name or node_id_str}"
            fields = [
                ("id", row.id_),
                ("name", row.name),
                ("python_path", row.python_path),
                ("version", row.version),
                ("status", node_data.get("status")),
                ("execution_id", row.execution_id),
                ("overrides", row.overrides),
                ("data_registry_id", row.data_registry_id),
                ("ceci_stage_schema_node_id", row.ceci_stage_schema_node_id),
            ]
        elif node_type == "ceci_file":
            row = provider.get_ops("ceci_file_node").get_row(UUID(node_id_str))
            title = f"File: {row.arg_name or node_id_str}"
            fields = [
                ("id", row.id_),
                ("path", row.path),
                ("arg_name", row.arg_name),
                ("execution_id", row.execution_id),
                ("data_registry_id", row.data_registry_id),
                ("description", row.description),
                ("ceci_file_schema_node_id", row.ceci_file_schema_node_id),
            ]
        else:
            return _PLACEHOLDER
    except Exception as e:
        return html.P(f"Error loading details: {e}", style={"color": "red"})

    return html.Div([
        html.H6(title, style={"marginTop": 0, "marginBottom": "10px", "color": "#333"}),
        html.Div([_kv_row(k, v) for k, v in fields]),
    ])
