"""CECI stage templates page."""

import dash
from plombiere.models.nodes import CeciStage, CeciStageCreate

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/ceci-stage", name="CECI Stages")

config = CrudPageConfig(
    entity_name="ceci_stage",
    display_name="CECI Stages",
    response_model=CeciStage,
    create_model=CeciStageCreate,
    table_columns=["id_", "name", "python_path", "version"],
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
