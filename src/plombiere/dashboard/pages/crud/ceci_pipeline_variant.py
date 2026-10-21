"""CECI pipeline variants page."""

import dash
from plombiere.models.ceci_pipelines import CeciPipelineVariant, CeciPipelineVariantCreate

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/ceci-pipeline-variant", name="CECI Pipeline Variants")

config = CrudPageConfig(
    entity_name="ceci_pipeline_variant",
    display_name="CECI Pipeline Variants",
    response_model=CeciPipelineVariant,
    create_model=CeciPipelineVariantCreate,
    table_columns=["id_", "name", "extra_description", "ceci_pipeline_id"],
    foreign_keys={"ceci_pipeline_id": "ceci_pipeline"},
    dag_path="/dag/variant",
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
