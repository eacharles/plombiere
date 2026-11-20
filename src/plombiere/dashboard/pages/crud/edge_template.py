"""Edge templates page."""

import dash
from tisserande.models.edges import EdgeTemplate, EdgeTemplateCreate

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/edge-template", name="Edge Templates")

config = CrudPageConfig(
    entity_name="edge_template",
    display_name="Edge Templates",
    response_model=EdgeTemplate,
    create_model=EdgeTemplateCreate,
    table_columns=["id_", "from_id", "to_id", "arg_name"],
    has_create=False,
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
