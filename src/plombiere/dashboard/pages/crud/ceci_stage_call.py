"""CECI stage call nodes page (schema and instance nodes)."""

import dash
from plombiere.models.nodes import CeciStageCall

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/ceci-stage-call", name="CECI Stage Calls")

config = CrudPageConfig(
    entity_name="ceci_stage_call",
    display_name="CECI Stage Calls",
    response_model=CeciStageCall,
    create_model=None,
    table_columns=["uid_", "node_type", "name", "status"],
    has_create=False,
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
