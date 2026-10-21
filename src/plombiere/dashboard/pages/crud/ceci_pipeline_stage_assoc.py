"""CECI pipeline ↔ stage schema node association page."""

import dash
from plombiere.models.ceci_assocs import CeciPipelineStageAssoc, CeciPipelineStageAssocCreate

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/ceci-pipeline-stage-assoc", name="Stage Associations")

config = CrudPageConfig(
    entity_name="ceci_pipeline_stage_assoc",
    display_name="Pipeline ↔ Stage Associations",
    response_model=CeciPipelineStageAssoc,
    create_model=CeciPipelineStageAssocCreate,
    table_columns=["id_", "ceci_pipeline_id", "ceci_stage_node_id"],
    foreign_keys={
        "ceci_pipeline_id": "ceci_pipeline",
        "ceci_stage_node_id": "ceci_stage_node",
    },
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
