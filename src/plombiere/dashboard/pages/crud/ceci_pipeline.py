"""CECI pipeline definitions page."""

import dash
from plombiere.models.ceci_pipelines import CeciPipeline, CeciPipelineCreate

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/ceci-pipeline", name="CECI Pipelines")

config = CrudPageConfig(
    entity_name="ceci_pipeline",
    display_name="CECI Pipelines",
    response_model=CeciPipeline,
    create_model=CeciPipelineCreate,
    table_columns=["id_", "name", "description"],
    dag_path="/dag/pipeline",
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
