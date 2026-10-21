"""Top-level app layout with sidebar navigation and page container."""

from dash import dcc, html, page_container

from .nav import create_sidebar


def create_layout() -> html.Div:
    """Create the top-level layout with sidebar + page content."""
    return html.Div(
        [
            dcc.Store(id="backend-settings", storage_type="local"),
            dcc.Location(id="url", refresh=False),
            html.Div(
                [
                    create_sidebar(),
                    html.Div(
                        page_container,
                        id="page-content",
                        style={
                            "flex": "1",
                            "padding": "20px",
                            "overflowY": "auto",
                            "height": "100vh",
                        },
                    ),
                ],
                style={"display": "flex", "height": "100vh"},
            ),
        ]
    )
