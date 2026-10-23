"""Variant DAG page — same topology as the parent pipeline, orange nodes have config overrides."""

import dash
import dash_cytoscape as cyto
from dash import Input, Output, State, callback, clientside_callback, dcc, html

from plombiere.backend import BackendProvider
from plombiere.dashboard.pages.dag._builders import DAG_LAYOUT, STYLESHEET, pipeline_elements

dash.register_page(__name__, path="/dag/variant", name="Variant DAG")

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
        provider = BackendProvider.get()
        variants = provider.get_ops("ceci_pipeline_variant").get_rows()
        pipelines = {p.id_: p.name for p in provider.get_ops("ceci_pipeline").get_rows()}
        options = [
            {"label": f"{v.name}  (pipeline: {pipelines.get(v.ceci_pipeline_id, v.ceci_pipeline_id)})", "value": v.id_}
            for v in variants
        ]
    except Exception:
        options = []

    preselect = None
    if "id" in kwargs:
        try:
            preselect = int(kwargs["id"])
        except (ValueError, TypeError):
            pass

    return html.Div([
        html.H2("Variant DAG"),
        html.P(
            "Orange nodes have configuration overrides. Right-click a node to see its details.",
            style={"color": "#888", "fontSize": "13px"},
        ),
        html.Hr(),
        dcc.Dropdown(
            id="dag-variant-select",
            options=options,
            value=preselect,
            placeholder="Select a variant…",
            style={"maxWidth": "600px"},
        ),
        html.Div(
            [
                html.Div(id="dag-variant-graph-container", style={"flex": "1 1 0%", "minWidth": 0, "marginTop": "16px"}),
                html.Div(id="dag-variant-detail-panel", children=_PLACEHOLDER, style=_DETAIL_PANEL_STYLE),
            ],
            style={"display": "flex", "gap": "0", "alignItems": "flex-start"},
        ),
        dcc.Store(id="dag-variant-hovered-node"),
        dcc.Store(id="dag-variant-rightclick-node"),
        html.Button(id="dag-variant-rightclick-trigger", n_clicks=0, style={"display": "none"}),
    ])


@callback(
    Output("dag-variant-graph-container", "children"),
    Input("dag-variant-select", "value"),
)
def render_variant_dag(variant_id):
    if variant_id is None:
        return html.P("Select a variant above.", style={"color": "#888", "fontStyle": "italic"})
    try:
        provider = BackendProvider.get()
        variant = provider.get_ops("ceci_pipeline_variant").get_row(variant_id)
        pipeline = provider.get_ops("ceci_pipeline").get_row(variant.ceci_pipeline_id)
        elements = pipeline_elements(pipeline.structure, overrides=variant.overrides)
        if not elements:
            return html.P("No stages found in this pipeline.")
        return cyto.Cytoscape(
            id="dag-variant-graph",
            elements=elements,
            layout=DAG_LAYOUT,
            style={"width": "100%", "height": "620px", "border": "1px solid #dee2e6", "borderRadius": "4px"},
            stylesheet=STYLESHEET,
        )
    except Exception as e:
        return html.P(f"Error: {e}", style={"color": "red"})


clientside_callback(
    "function(d) { return d != null ? d : window.dash_clientside.no_update; }",
    Output("dag-variant-hovered-node", "data"),
    Input("dag-variant-graph", "mouseoverNodeData"),
    prevent_initial_call=True,
)

clientside_callback(
    "function(n, h) { if (n && h) return h; return window.dash_clientside.no_update; }",
    Output("dag-variant-rightclick-node", "data"),
    Input("dag-variant-rightclick-trigger", "n_clicks"),
    State("dag-variant-hovered-node", "data"),
    prevent_initial_call=True,
)


@callback(
    Output("dag-variant-detail-panel", "children"),
    Input("dag-variant-rightclick-node", "data"),
    prevent_initial_call=True,
)
def show_variant_node_detail(node_data):
    if not node_data:
        return _PLACEHOLDER
    node_type = node_data.get("node_type")
    if node_type == "stage":
        title = f"Stage: {node_data.get('stage_name', '?')}"
        aliases = node_data.get("aliases") or {}
        overrides = node_data.get("overrides")
        fields = [
            ("name", node_data.get("stage_name")),
            ("classname", node_data.get("classname")),
            ("aliases", ", ".join(f"{k}→{v}" for k, v in aliases.items()) or "—"),
            ("overrides", overrides if overrides else "—"),
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
