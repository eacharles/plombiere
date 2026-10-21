"""Provenance executions page."""

import dash
from tisserande.models.execution import Execution, ExecutionCreate

from plombiere.dashboard.pages.crud._base import CrudPageConfig, make_crud_layout, register_crud_callbacks

dash.register_page(__name__, path="/crud/execution", name="Executions")

config = CrudPageConfig(
    entity_name="execution",
    display_name="Executions",
    response_model=Execution,
    create_model=ExecutionCreate,
    table_columns=["id_", "parent_execution_id", "status", "start_time", "duration_seconds"],
    has_create=False,
    foreign_keys={"parent_execution_id": "execution"},
)

layout = make_crud_layout(config)
register_crud_callbacks(config)
