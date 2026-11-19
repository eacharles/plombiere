"""CECI stage nodes page (schema and instance nodes)."""

import dash
from plombiere.models.nodes import CeciStageNode

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/ceci-stage-node", name="CECI Stage Nodes")

config = CrudPageConfig(
    entity_name="ceci_stage_node",
    display_name="CECI Stage Nodes",
    response_model=CeciStageNode,
    create_model=None,
    table_columns=["uid_", "node_type", "name", "status"],
    has_create=False,
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
