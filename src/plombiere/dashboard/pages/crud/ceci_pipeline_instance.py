"""CECI pipeline execution instances page."""

import dash
from plombiere.models.ceci_pipelines import CeciPipelineInstance, CeciPipelineInstanceCreate

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/ceci-pipeline-instance", name="CECI Pipeline Instances")

config = CrudPageConfig(
    entity_name="ceci_pipeline_instance",
    display_name="CECI Pipeline Instances",
    response_model=CeciPipelineInstance,
    create_model=CeciPipelineInstanceCreate,
    table_columns=["id_", "status", "run_date", "execution_id", "ceci_pipeline_variant_id"],
    foreign_keys={"ceci_pipeline_variant_id": "ceci_pipeline_variant"},
    dag_path="/dag/instance",
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
