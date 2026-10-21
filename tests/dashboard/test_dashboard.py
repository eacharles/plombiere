"""Dash integration tests for the Plombiere dashboard.

Requires Chrome and selenium.  Run with:
    pytest tests/dashboard/ -v

Each test starts the Dash server on a random port via dash_duo and drives it
with a headless Chrome browser.
"""

from __future__ import annotations

import pytest

selenium = pytest.importorskip("selenium", reason="selenium not installed")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TIMEOUT = 30  # seconds to wait for Dash callbacks / page transitions


def _goto(dash_duo, path: str) -> None:
    """Navigate to a dashboard path and wait for the page container."""
    dash_duo.driver.get(f"{dash_duo.server_url}{path}")
    dash_duo.wait_for_element("#page-content", timeout=_TIMEOUT)


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------


class TestSmoke:
    """Basic page load and sidebar checks."""

    def test_home_page_loads(self, dash_duo, dash_app):
        dash_duo.start_server(dash_app)
        dash_duo.wait_for_element("h4", timeout=_TIMEOUT)
        assert "Plombiere" in dash_duo.find_element("h4").text

    def test_navigate_to_pipelines_page(self, dash_duo, dash_app):
        dash_duo.start_server(dash_app)
        _goto(dash_duo, "/crud/ceci-pipeline")
        dash_duo.wait_for_text_to_equal("h2", "CECI Pipelines", timeout=_TIMEOUT)


# ---------------------------------------------------------------------------
# CRUD: pipelines table
# ---------------------------------------------------------------------------


class TestCrudPipelinesPage:
    """CRUD table for CeciPipeline."""

    def test_table_row_loads(self, dash_duo, dash_app):
        dash_duo.start_server(dash_app)
        _goto(dash_duo, "/crud/ceci-pipeline")
        # AG Grid renders rows once the refresh callback fires
        dash_duo.wait_for_element(".ag-row", timeout=_TIMEOUT)
        rows = dash_duo.find_elements(".ag-row")
        assert len(rows) >= 1

    def test_view_dag_button_present(self, dash_duo, dash_app):
        dash_duo.start_server(dash_app)
        _goto(dash_duo, "/crud/ceci-pipeline")
        dash_duo.wait_for_element("#ceci_pipeline-dag-btn", timeout=_TIMEOUT)
        btn = dash_duo.find_element("#ceci_pipeline-dag-btn")
        assert btn.text == "View DAG"

    def test_view_dag_button_navigates(self, dash_duo, dash_app):
        dash_duo.start_server(dash_app)
        _goto(dash_duo, "/crud/ceci-pipeline")
        dash_duo.wait_for_element(".ag-row", timeout=_TIMEOUT)
        # Select the first data row via its checkbox
        checkbox = dash_duo.find_element(".ag-row[row-index='0'] .ag-checkbox-input")
        checkbox.click()
        # Click View DAG — clientside_callback sets window.location.href
        dash_duo.find_element("#ceci_pipeline-dag-btn").click()
        dash_duo.wait_for_text_to_equal("h2", "Pipeline DAG", timeout=_TIMEOUT)
        assert "id=" in dash_duo.driver.current_url


# ---------------------------------------------------------------------------
# CRUD: variants table
# ---------------------------------------------------------------------------


class TestCrudVariantsPage:
    def test_table_row_loads(self, dash_duo, dash_app):
        dash_duo.start_server(dash_app)
        _goto(dash_duo, "/crud/ceci-pipeline-variant")
        dash_duo.wait_for_element(".ag-row", timeout=_TIMEOUT)
        assert len(dash_duo.find_elements(".ag-row")) >= 1


# ---------------------------------------------------------------------------
# CRUD: detail modal, create modal, delete feedback
# (placed here — before the resource-heavy DAG pages — so they run in a
#  clean environment and aren't affected by Cytoscape graph rendering)
# ---------------------------------------------------------------------------


class TestCrudDetailModal:
    def test_name_cell_click_opens_modal(self, dash_duo, dash_app):
        dash_duo.start_server(dash_app)
        _goto(dash_duo, "/crud/ceci-pipeline")
        dash_duo.wait_for_element(".ag-row", timeout=_TIMEOUT)
        dash_duo.find_element(".ag-row[row-index='0'] .ag-cell[col-id='name']").click()
        dash_duo.wait_for_text_to_equal(
            "#ceci_pipeline-detail-title", "CECI Pipelines: test_pipeline", timeout=_TIMEOUT
        )

    def test_detail_modal_closes(self, dash_duo, dash_app):
        dash_duo.start_server(dash_app)
        _goto(dash_duo, "/crud/ceci-pipeline")
        dash_duo.wait_for_element(".ag-row", timeout=_TIMEOUT)
        dash_duo.find_element(".ag-row[row-index='0'] .ag-cell[col-id='name']").click()
        dash_duo.wait_for_text_to_equal(
            "#ceci_pipeline-detail-title", "CECI Pipelines: test_pipeline", timeout=_TIMEOUT
        )
        dash_duo.find_element("#ceci_pipeline-detail-close").click()
        dash_duo.wait_for_text_to_equal("#ceci_pipeline-detail-title", "", timeout=_TIMEOUT)


class TestCrudCreateModal:
    def test_create_btn_opens_modal(self, dash_duo, dash_app):
        dash_duo.start_server(dash_app)
        _goto(dash_duo, "/crud/ceci-pipeline")
        dash_duo.find_element("#ceci_pipeline-create-btn").click()
        dash_duo.wait_for_element("#ceci_pipeline-create-modal", timeout=_TIMEOUT)
        assert dash_duo.find_element("#ceci_pipeline-create-modal").is_displayed()

    def test_create_modal_closes(self, dash_duo, dash_app):
        dash_duo.start_server(dash_app)
        _goto(dash_duo, "/crud/ceci-pipeline")
        dash_duo.find_element("#ceci_pipeline-create-btn").click()
        dash_duo.wait_for_element("#ceci_pipeline-create-modal", timeout=_TIMEOUT)
        dash_duo.find_element("#ceci_pipeline-modal-close").click()
        import time; time.sleep(0.5)
        assert not dash_duo.find_element("#ceci_pipeline-create-modal").is_displayed()


# ---------------------------------------------------------------------------
# DAG pages
# ---------------------------------------------------------------------------


class TestPipelineDagPage:
    def test_page_loads(self, dash_duo, dash_app):
        dash_duo.start_server(dash_app)
        _goto(dash_duo, "/dag/pipeline")
        dash_duo.wait_for_text_to_equal("h2", "Pipeline DAG", timeout=_TIMEOUT)

    def test_preselect_via_url_param(self, dash_duo, dash_app):
        """?id=1 should pre-select the pipeline and render the graph."""
        dash_duo.start_server(dash_app)
        _goto(dash_duo, "/dag/pipeline?id=1")
        dash_duo.wait_for_element("#dag-pipeline-graph canvas", timeout=_TIMEOUT)


class TestVariantDagPage:
    def test_preselect_via_url_param(self, dash_duo, dash_app):
        dash_duo.start_server(dash_app)
        _goto(dash_duo, "/dag/variant?id=1")
        dash_duo.wait_for_element("#dag-variant-graph canvas", timeout=_TIMEOUT)


class TestInstanceDagPage:
    def test_instance_dag_renders(self, dash_duo, dash_app):
        """Navigate directly to the instance DAG via URL param — graph should render."""
        from plombiere.backend import BackendProvider

        dash_duo.start_server(dash_app)
        instances = BackendProvider.get().get_ops("ceci_pipeline_instance").get_rows()
        assert len(instances) >= 1, "Expected at least one instance in test DB"
        instance_id = str(instances[0].id_)
        _goto(dash_duo, f"/dag/instance?id={instance_id}")
        dash_duo.wait_for_element("#dag-instance-graph canvas", timeout=_TIMEOUT)


# ---------------------------------------------------------------------------
# CRUD: delete (placed last so the variant deletion doesn't affect DAG tests)
# ---------------------------------------------------------------------------


class TestCrudDelete:
    def test_delete_without_selection_shows_warning(self, dash_duo, dash_app):
        dash_duo.start_server(dash_app)
        _goto(dash_duo, "/crud/ceci-pipeline")
        dash_duo.wait_for_element(".ag-row", timeout=_TIMEOUT)
        dash_duo.find_element("#ceci_pipeline-delete-btn").click()
        dash_duo.wait_for_text_to_equal(
            "#ceci_pipeline-status", "No row selected.", timeout=_TIMEOUT
        )
