"""Dash application factory."""

from pathlib import Path

import dash_cytoscape as cyto
from dash import Dash

from .layout import create_layout

cyto.load_extra_layouts()


def create_app(debug: bool = False) -> Dash:  # noqa: FBT001, FBT002
    """Create the multi-page Dash application."""
    pages_dir = Path(__file__).parent / "pages"
    assets_dir = Path(__file__).parent / "assets"

    app = Dash(
        __name__,
        use_pages=True,
        pages_folder=str(pages_dir),
        assets_folder=str(assets_dir),
        suppress_callback_exceptions=True,
        title="Plombiere Dashboard",
    )

    app.layout = create_layout()
    return app
