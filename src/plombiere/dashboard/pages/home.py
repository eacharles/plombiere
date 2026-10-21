"""Home / landing page."""

import dash
from dash import Input, Output, callback, html

from plombiere.backend import BackendProvider

dash.register_page(__name__, path="/", name="Home")


def layout(**kwargs):
    return html.Div(
        [
            html.H2("Plombiere Dashboard"),
            html.P("CECI pipeline provenance tracking built on tisserande."),
            html.Hr(),
            html.Div(id="home-status"),
        ]
    )


@callback(Output("home-status", "children"), Input("backend-settings", "data"))
def update_status(settings_data):
    provider = BackendProvider.get()
    db_url = provider.settings.db_url

    try:
        n_nodes = provider.get_ops("node").count_rows()
        n_exec = provider.get_ops("execution").count_rows()
        n_pipelines = provider.get_ops("ceci_pipeline").count_rows()
        status = html.Span("Connected", style={"color": "green"})
        counts = html.Ul(
            [
                html.Li(f"Nodes: {n_nodes}"),
                html.Li(f"Executions: {n_exec}"),
                html.Li(f"CECI Pipelines: {n_pipelines}"),
            ]
        )
    except Exception as e:
        status = html.Span(f"Error: {e}", style={"color": "red"})
        counts = html.Div()

    return html.Div(
        [
            html.H5("Status"),
            html.P([html.Strong("Database: "), db_url]),
            html.P([html.Strong("Connection: "), status]),
            counts,
        ]
    )
