"""All provenance nodes page."""

import dash
from tisserande.models import Node, NodeCreate

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/node", name="Nodes")

config = CrudPageConfig(
    entity_name="node",
    display_name="All Nodes",
    response_model=Node,
    create_model=NodeCreate,
    table_columns=["uid_", "node_type", "node_template_id"],
    has_create=False,
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
