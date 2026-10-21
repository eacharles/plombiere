"""Variant DAG page — same topology as the parent pipeline, orange nodes have config overrides."""

import dash
import dash_cytoscape as cyto
from dash import Input, Output, callback, dcc, html

from plombiere.backend import BackendProvider
from plombiere.dashboard.pages.dag._builders import DAG_LAYOUT, STYLESHEET, pipeline_elements

dash.register_page(__name__, path="/dag/variant", name="Variant DAG")


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
            "Orange nodes have configuration overrides in this variant.",
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
        html.Div(id="dag-variant-graph-container", style={"marginTop": "16px"}),
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
