"""CECI file type templates page."""

import dash
from plombiere.models.nodes import CeciFileType, CeciFileTypeCreate

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/ceci-file-type", name="CECI File Types")

config = CrudPageConfig(
    entity_name="ceci_file_type",
    display_name="CECI File Types",
    response_model=CeciFileType,
    create_model=CeciFileTypeCreate,
    table_columns=["id_", "name", "version", "description"],
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
