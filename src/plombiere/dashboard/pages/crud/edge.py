"""Provenance edges page."""

import dash
from tisserande.models.edges import Edge, EdgeCreate

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/edge", name="Edges")

config = CrudPageConfig(
    entity_name="edge",
    display_name="Edges",
    response_model=Edge,
    create_model=EdgeCreate,
    table_columns=["id_", "from_id", "to_id", "execution_id"],
    has_create=False,
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
