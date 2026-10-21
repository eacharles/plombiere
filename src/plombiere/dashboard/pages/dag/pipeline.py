"""Pipeline DAG page — shows stage topology from the pipeline YAML structure."""

import dash
import dash_cytoscape as cyto
from dash import Input, Output, callback, dcc, html

from plombiere.backend import BackendProvider
from plombiere.dashboard.pages.dag._builders import DAG_LAYOUT, STYLESHEET, pipeline_elements

dash.register_page(__name__, path="/dag/pipeline", name="Pipeline DAG")


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
        html.Hr(),
        dcc.Dropdown(
            id="dag-pipeline-select",
            options=options,
            value=preselect,
            placeholder="Select a pipeline…",
            style={"maxWidth": "500px"},
        ),
        html.Div(id="dag-pipeline-graph-container", style={"marginTop": "16px"}),
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
