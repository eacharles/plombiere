"""Sidebar navigation component."""

from dash import dcc, html

SIDEBAR_STYLE = {
    "width": "220px",
    "backgroundColor": "#f8f9fa",
    "padding": "20px 10px",
    "borderRight": "1px solid #dee2e6",
    "overflowY": "auto",
    "height": "100vh",
}

LINK_STYLE = {
    "display": "block",
    "padding": "6px 12px",
    "textDecoration": "none",
    "color": "#333",
    "borderRadius": "4px",
    "marginBottom": "2px",
}

SECTION_STYLE = {
    "fontSize": "11px",
    "fontWeight": "bold",
    "textTransform": "uppercase",
    "color": "#888",
    "padding": "12px 12px 4px",
    "letterSpacing": "0.5px",
}


def _nav_link(label: str, href: str) -> dcc.Link:
    return dcc.Link(label, href=href, style=LINK_STYLE)


def _section_header(label: str) -> html.Div:
    return html.Div(label, style=SECTION_STYLE)


def create_sidebar() -> html.Div:
    """Create the sidebar navigation."""
    return html.Div(
        [
            html.H4("Plombiere", style={"padding": "0 12px", "marginBottom": "20px"}),
            _nav_link("Home", "/"),
            _section_header("Provenance"),
            _nav_link("Nodes", "/crud/node"),
            _nav_link("Edges", "/crud/edge"),
            _nav_link("Executions", "/crud/execution"),
            _section_header("CECI Nodes"),
            _nav_link("CECI File Nodes", "/crud/ceci-file-node"),
            _nav_link("CECI Stage Nodes", "/crud/ceci-stage-node"),
            _section_header("CECI Pipelines"),
            _nav_link("Pipelines", "/crud/ceci-pipeline"),
            _nav_link("Variants", "/crud/ceci-pipeline-variant"),
            _nav_link("Instances", "/crud/ceci-pipeline-instance"),
            _nav_link("Stage Associations", "/crud/ceci-pipeline-stage-assoc"),
            _section_header("DAG Views"),
            _nav_link("Pipeline DAG", "/dag/pipeline"),
            _nav_link("Variant DAG", "/dag/variant"),
            _nav_link("Instance DAG", "/dag/instance"),
        ],
        style=SIDEBAR_STYLE,
    )
