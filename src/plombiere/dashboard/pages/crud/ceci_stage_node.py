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
    table_columns=["id_", "type_", "arg_name", "execution_id"],
    has_create=False,
    foreign_keys={"execution_id": "execution"},
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
