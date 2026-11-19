"""CECI file nodes page (schema and instance nodes)."""

import dash
from plombiere.models.nodes import CeciFile

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/ceci-file", name="CECI Files")

config = CrudPageConfig(
    entity_name="ceci_file",
    display_name="CECI Files",
    response_model=CeciFile,
    create_model=None,
    table_columns=["uid_", "node_type", "file_path", "creator"],
    has_create=False,
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
