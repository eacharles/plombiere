"""Association templates page."""

import dash
from tisserande.models.associations import AssocTemplate, AssocTemplateCreate

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/assoc-template", name="Assoc Templates")

config = CrudPageConfig(
    entity_name="assoc_template",
    display_name="Association Templates",
    response_model=AssocTemplate,
    create_model=AssocTemplateCreate,
    table_columns=["id_", "node_template_id", "graph_template_id"],
    has_create=False,
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
