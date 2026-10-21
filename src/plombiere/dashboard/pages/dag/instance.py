"""Instance DAG page — shows actual stage and file nodes from a pipeline run."""

import dash
import dash_cytoscape as cyto
from dash import Input, Output, callback, dcc, html

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
            "Stage nodes are coloured by execution status. File nodes show data handles.",
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
        html.Div(id="dag-instance-graph-container", style={"marginTop": "16px"}),
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
