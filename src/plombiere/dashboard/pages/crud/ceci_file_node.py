"""CECI file nodes page (schema and instance nodes)."""

import dash
from plombiere.models.nodes import CeciFileNode

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/ceci-file-node", name="CECI File Nodes")

config = CrudPageConfig(
    entity_name="ceci_file_node",
    display_name="CECI File Nodes",
    response_model=CeciFileNode,
    create_model=None,
    table_columns=["id_", "type_", "arg_name", "execution_id"],
    has_create=False,
    foreign_keys={"execution_id": "execution"},
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
