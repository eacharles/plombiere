"""All provenance nodes page."""

import dash
from tisserande.models.nodes import AnyNodeCreate, Node

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/node", name="Nodes")

config = CrudPageConfig(
    entity_name="node",
    display_name="All Nodes",
    response_model=Node,
    create_model=AnyNodeCreate,
    table_columns=["id_", "type_", "arg_name", "execution_id"],
    has_create=False,
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
