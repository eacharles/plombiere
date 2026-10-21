"""CRUD page factory: generates a complete page layout + callbacks from config."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from dash import Input, Output, State, callback, clientside_callback, ctx, dcc, html, no_update
from pydantic import BaseModel

from plombiere.backend import BackendProvider
from plombiere.dashboard.pages.crud._components import (
    build_action_bar,
    build_create_modal,
    build_data_table,
    build_detail_modal,
    build_filter_bar,
)

# Maps FK column names to entity names recognised by BackendProvider.get_ops()
FK_COLUMN_MAP: dict[str, str] = {
    "execution_id": "execution",
    "parent_execution_id": "execution",
    "ceci_pipeline_id": "ceci_pipeline",
    "ceci_pipeline_variant_id": "ceci_pipeline_variant",
    "ceci_stage_node_id": "ceci_stage_node",
    "ceci_file_schema_node_id": "ceci_file_node",
    "ceci_stage_schema_node_id": "ceci_stage_node",
}


def _serialize_value(val: Any) -> Any:
    """Convert non-JSON-serialisable values to strings for the DataTable."""
    if val is None or isinstance(val, (str, int, float, bool)):
        return val
    return str(val)


def _build_detail_content(row: Any) -> html.Div:
    """Build a formatted display of all fields on a pydantic model instance."""
    items = []
    for field_name in type(row).model_fields:
        value = getattr(row, field_name, None)
        display_val = str(value) if value is not None else "—"
        items.append(
            html.Div(
                [
                    html.Span(
                        field_name,
                        style={
                            "fontWeight": "600",
                            "width": "200px",
                            "display": "inline-block",
                            "color": "#555",
                            "fontSize": "13px",
                        },
                    ),
                    html.Span(
                        display_val,
                        style={"fontSize": "13px", "wordBreak": "break-all"},
                    ),
                ],
                style={"padding": "6px 0", "borderBottom": "1px solid #f0f0f0"},
            )
        )
    return html.Div(items)


def _parse_id(raw: Any) -> Any:
    """Parse a row ID as int or UUID depending on the value."""
    if raw is None:
        return None
    try:
        return int(raw)
    except (ValueError, TypeError):
        pass
    try:
        return UUID(str(raw))
    except (ValueError, AttributeError):
        return raw


@dataclass
class CrudPageConfig:
    entity_name: str
    display_name: str
    response_model: type[BaseModel]
    create_model: type[BaseModel] | None
    table_columns: list[str]
    has_create: bool = True
    multi_select: bool = False
    extra_layout: list | None = None
    foreign_keys: dict[str, str] = field(default_factory=dict)
    dag_path: str | None = None


def make_crud_layout(config: CrudPageConfig):
    """Generate the page layout function for a CRUD entity."""
    prefix = config.entity_name

    def layout_fn(**kwargs):
        children = [
            html.H2(config.display_name),
            html.Hr(),
            build_action_bar(prefix, has_create=config.has_create, dag_path=config.dag_path),
            html.Div(id=f"{prefix}-status", style={"marginBottom": "8px"}),
            build_filter_bar(prefix),
            build_data_table(f"{prefix}-table", config.table_columns, multi_select=config.multi_select),
            build_detail_modal(prefix),
            dcc.Store(id=f"{prefix}-all-data", data=[]),
        ]
        if config.has_create and config.create_model is not None:
            children.insert(
                -1,
                build_create_modal(prefix, config.create_model, config.foreign_keys),
            )
        if config.extra_layout:
            children.extend(config.extra_layout)
        if config.dag_path:
            children.append(dcc.Store(id=f"{prefix}-dag-nav-dummy"))
        return html.Div(children)

    return layout_fn


def register_crud_callbacks(config: CrudPageConfig) -> None:
    """Register all Dash callbacks for a CRUD page."""
    prefix = config.entity_name

    @callback(
        Output(f"{prefix}-all-data", "data"),
        Input(f"{prefix}-refresh-btn", "n_clicks"),
        prevent_initial_call=False,
    )
    def refresh_table(n_clicks):
        try:
            ops = BackendProvider.get().get_ops(config.entity_name)
            rows = ops.get_rows()
            return [
                {col: _serialize_value(getattr(row, col, None)) for col in config.table_columns}
                for row in rows
            ]
        except Exception:
            return []

    @callback(
        Output(f"{prefix}-table", "rowData"),
        Input(f"{prefix}-filter-input", "value"),
        Input(f"{prefix}-all-data", "data"),
    )
    def filter_table(filter_text, all_data):
        if not all_data:
            return []
        if not filter_text:
            return all_data
        query = filter_text.lower()
        return [
            row for row in all_data if any(query in str(v).lower() for v in row.values() if v is not None)
        ]

    @callback(
        Output(f"{prefix}-detail-modal", "style"),
        Output(f"{prefix}-detail-title", "children"),
        Output(f"{prefix}-detail-content", "children"),
        Input(f"{prefix}-table", "cellClicked"),
        Input(f"{prefix}-detail-close", "n_clicks"),
        State(f"{prefix}-table", "rowData"),
        State(f"{prefix}-detail-modal", "style"),
        prevent_initial_call=True,
    )
    def show_detail(cell_clicked, close_clicks, row_data_list, modal_style):
        triggered_prop = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
        if "detail-close" in triggered_prop:
            return {**modal_style, "display": "none"}, no_update, no_update

        if not cell_clicked:
            return no_update, no_update, no_update

        col_id = cell_clicked.get("colId")
        row_index = cell_clicked.get("rowIndex")

        clickable = col_id == "name" or (col_id in FK_COLUMN_MAP)
        if not clickable:
            return no_update, no_update, no_update

        if row_data_list is None or row_index is None or row_index >= len(row_data_list):
            return no_update, no_update, no_update
        row_data = row_data_list[row_index]

        try:
            provider = BackendProvider.get()

            if col_id == "name":
                row_id = _parse_id(row_data.get("id_"))
                ops = provider.get_ops(config.entity_name)
                full_row = ops.get_row(row_id)
                title = f"{config.display_name}: {getattr(full_row, 'name', row_id)}"
                content = _build_detail_content(full_row)
            else:
                ref_entity = FK_COLUMN_MAP[col_id]
                ref_id = _parse_id(row_data.get(col_id))
                if ref_id is None:
                    return no_update, no_update, no_update
                ops = provider.get_ops(ref_entity)
                full_row = ops.get_row(ref_id)
                title = f"{ref_entity.replace('_', ' ').title()}: {getattr(full_row, 'name', ref_id)}"
                content = _build_detail_content(full_row)

        except Exception as e:
            title = "Error"
            content = html.P(f"Could not load details: {e}", style={"color": "red"})

        return {**modal_style, "display": "block"}, title, content

    if config.has_create and config.create_model is not None:
        @callback(
            Output(f"{prefix}-create-modal", "style"),
            Input(f"{prefix}-create-btn", "n_clicks"),
            Input(f"{prefix}-modal-close", "n_clicks"),
            State(f"{prefix}-create-modal", "style"),
            prevent_initial_call=True,
        )
        def toggle_modal(open_clicks, close_clicks, current_style):
            if ctx.triggered_id == f"{prefix}-create-btn":
                return {**current_style, "display": "block"}
            return {**current_style, "display": "none"}

        field_names = list(config.create_model.model_fields.keys())
        field_inputs = [State(f"{prefix}-field-{name}", "value") for name in field_names]

        @callback(
            Output(f"{prefix}-create-status", "children"),
            Output(f"{prefix}-refresh-btn", "n_clicks", allow_duplicate=True),
            Input(f"{prefix}-create-submit", "n_clicks"),
            *field_inputs,
            State(f"{prefix}-refresh-btn", "n_clicks"),
            prevent_initial_call=True,
        )
        def create_entity(n_clicks, *args):
            field_values = args[: len(field_names)]
            refresh_clicks = args[-1]

            kwargs: dict[str, Any] = {}
            for name, value in zip(field_names, field_values):
                field_info = config.create_model.model_fields[name]  # type: ignore[union-attr]
                if value is None or value == "" or value == []:
                    if field_info.is_required():
                        return html.Span(f"Field '{name}' is required.", style={"color": "red"}), no_update
                    continue

                annotation = field_info.annotation
                if annotation is bool:
                    kwargs[name] = bool(value)
                elif annotation is int:
                    kwargs[name] = int(value)
                elif annotation is dict or str(annotation).startswith("dict"):
                    try:
                        kwargs[name] = json.loads(value)
                    except json.JSONDecodeError:
                        return html.Span(f"Invalid JSON for '{name}'.", style={"color": "red"}), no_update
                else:
                    kwargs[name] = value

            try:
                ops = BackendProvider.get().get_ops(config.entity_name)
                result = ops.create_row(**kwargs)
                return (
                    html.Span(f"Created: {getattr(result, 'name', result.id_)}", style={"color": "green"}),
                    (refresh_clicks or 0) + 1,
                )
            except Exception as e:
                return html.Span(f"Error: {e}", style={"color": "red"}), no_update

    @callback(
        Output(f"{prefix}-status", "children"),
        Output(f"{prefix}-refresh-btn", "n_clicks", allow_duplicate=True),
        Input(f"{prefix}-delete-btn", "n_clicks"),
        State(f"{prefix}-table", "selectedRows"),
        State(f"{prefix}-refresh-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def delete_entity(n_clicks, selected_rows, refresh_clicks):
        if not selected_rows:
            return html.Span("No row selected.", style={"color": "orange"}), no_update

        row_data = selected_rows[0]
        row_id = _parse_id(row_data.get("id_"))
        if row_id is None:
            return html.Span("Cannot determine row ID.", style={"color": "red"}), no_update

        try:
            ops = BackendProvider.get().get_ops(config.entity_name)
            ops.delete_row(row_id)
            return (
                html.Span(f"Deleted row {row_id}.", style={"color": "green"}),
                (refresh_clicks or 0) + 1,
            )
        except Exception as e:
            return html.Span(f"Error: {e}", style={"color": "red"}), no_update

    if config.dag_path:
        dag_path = config.dag_path
        clientside_callback(
            f"""
            function(n_clicks, selected_rows) {{
                if (!n_clicks || !selected_rows || selected_rows.length === 0) {{
                    return window.dash_clientside.no_update;
                }}
                var row_id = selected_rows[0]['id_'];
                if (row_id === null || row_id === undefined) {{
                    return window.dash_clientside.no_update;
                }}
                window.location.href = '{dag_path}?id=' + row_id;
                return window.dash_clientside.no_update;
            }}
            """,
            Output(f"{prefix}-dag-nav-dummy", "data"),
            Input(f"{prefix}-dag-btn", "n_clicks"),
            State(f"{prefix}-table", "selectedRows"),
            prevent_initial_call=True,
        )
