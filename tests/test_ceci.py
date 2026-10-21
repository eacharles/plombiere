"""Tests for CECI pipeline tables and ingestion utilities."""

from __future__ import annotations

import textwrap
from datetime import date
from pathlib import Path

import pytest

from plombiere.models import (
    CeciPipeline,
    CeciPipelineCreate,
    CeciPipelineInstance,
    CeciPipelineInstanceCreate,
    CeciPipelineStageAssoc,
    CeciPipelineStageAssocCreate,
    CeciPipelineVariant,
    CeciPipelineVariantCreate,
)
from plombiere.models.nodes import CeciFileNodeCreate, CeciStageNodeCreate
from plombiere.models.types import CeciNodeType
from tisserande.models.types import ExecutionStatus


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestCeciPipelineModels:
    def test_pipeline_create(self):
        obj = CeciPipelineCreate(name="pz", description="Photo-z", structure={"stages": []}, config={})
        assert obj.name == "pz"
        assert obj.structure == {"stages": []}

    def test_pipeline_response(self):
        obj = CeciPipeline(id_=1, name="pz", description="Photo-z", structure={}, config={})
        assert obj.id_ == 1
        assert "id_" in CeciPipeline.col_names_for_table

    def test_variant_create(self):
        obj = CeciPipelineVariantCreate(
            name="gold", extra_description="Gold sample", overrides={}, ceci_pipeline_id=1
        )
        assert obj.ceci_pipeline_id == 1

    def test_variant_response(self):
        obj = CeciPipelineVariant(
            id_=2, name="gold", extra_description="", overrides={}, ceci_pipeline_id=1
        )
        assert obj.id_ == 2

    def test_instance_create(self):
        obj = CeciPipelineInstanceCreate(
            status=ExecutionStatus.SUCCESS,
            run_date=date(2025, 7, 20),
            ceci_pipeline_variant_id=1,
        )
        assert obj.status == ExecutionStatus.SUCCESS

    def test_instance_response(self):
        import uuid

        CeciPipelineInstance(
            id_=uuid.uuid4(),
            status=ExecutionStatus.SUCCESS,
            run_date=date(2025, 7, 20),
            ceci_pipeline_variant_id=1,
        )
        assert "run_date" in CeciPipelineInstance.col_names_for_table

    def test_assoc_create(self):
        import uuid

        stage_id = uuid.uuid4()
        obj = CeciPipelineStageAssocCreate(ceci_pipeline_id=1, ceci_stage_node_id=stage_id)
        assert obj.ceci_pipeline_id == 1

    def test_assoc_response(self):
        import uuid

        stage_id = uuid.uuid4()
        obj = CeciPipelineStageAssoc(id_=1, ceci_pipeline_id=1, ceci_stage_node_id=stage_id)
        assert obj.id_ == 1


class TestCeciNodeTypes:
    def test_ceci_file_is_data(self):
        assert CeciNodeType.CECI_FILE.is_data
        assert not CeciNodeType.CECI_FILE.is_logic

    def test_ceci_stage_is_logic(self):
        assert CeciNodeType.CECI_STAGE.is_logic
        assert not CeciNodeType.CECI_STAGE.is_data

    def test_ceci_stage_node_create(self):
        obj = CeciStageNodeCreate(
            name="FlexZBoostEstimator",
            python_path="rail.estimation.algos.flexzboost.FlexZBoostEstimator",
        )
        assert obj.type_ == "ceci_stage"
        assert obj.python_path == "rail.estimation.algos.flexzboost.FlexZBoostEstimator"

    def test_ceci_file_node_create(self):
        obj = CeciFileNodeCreate(
            path="/tmp/output.hdf5",
            arg_name="output",
        )
        assert obj.type_ == "ceci_file"
        assert obj.arg_name == "output"


# ---------------------------------------------------------------------------
# DB / layer tests
# ---------------------------------------------------------------------------


class TestCeciPipelineLayer:
    """Integration tests exercising the full layer stack for CECI pipeline tables."""

    def test_create_and_get_pipeline(self):
        from plombiere.local_sync import ceci_pipeline

        row = ceci_pipeline.create_row(
            name="pz_dp1", description="Photo-z pipeline", structure={"stages": []}, config={}
        )
        assert row.id_ is not None
        assert row.name == "pz_dp1"

        rows = ceci_pipeline.get_rows()
        assert any(r.name == "pz_dp1" for r in rows)

    def test_create_variant(self):
        from plombiere.local_sync import ceci_pipeline, ceci_pipeline_variant

        pipeline_row = ceci_pipeline.create_row(
            name="pz_v2", description="", structure={}, config={}
        )
        variant_row = ceci_pipeline_variant.create_row(
            name="gold",
            extra_description="Gold sample variant",
            overrides={"some_param": 1},
            ceci_pipeline_id=pipeline_row.id_,
        )
        assert variant_row.ceci_pipeline_id == pipeline_row.id_
        assert variant_row.name == "gold"

    def test_create_instance(self):
        from plombiere.local_sync import ceci_pipeline, ceci_pipeline_instance, ceci_pipeline_variant

        pipeline_row = ceci_pipeline.create_row(
            name="pz_v3", description="", structure={}, config={}
        )
        variant_row = ceci_pipeline_variant.create_row(
            name="silver", extra_description="", overrides={}, ceci_pipeline_id=pipeline_row.id_
        )
        instance_row = ceci_pipeline_instance.create_row(
            status=ExecutionStatus.SUCCESS.value,
            run_date=date(2025, 7, 20),
            ceci_pipeline_variant_id=variant_row.id_,
        )
        assert instance_row.id_ is not None
        instances = ceci_pipeline_instance.get_rows()
        assert any(str(r.id_) == str(instance_row.id_) for r in instances)

    def test_create_stage_assoc(self):
        from plombiere.local_sync import ceci_pipeline, ceci_pipeline_stage_assoc
        from tisserande.local_sync import node

        pipeline_row = ceci_pipeline.create_row(
            name="pz_v4", description="", structure={}, config={}
        )
        stage_node_row = node.create_row(
            type_="ceci_stage",
            name="FZBoost",
            python_path="rail.algos.FZBoost",
        )
        assoc_row = ceci_pipeline_stage_assoc.create_row(
            ceci_pipeline_id=pipeline_row.id_,
            ceci_stage_node_id=stage_node_row.id_,
        )
        assert assoc_row.ceci_pipeline_id == pipeline_row.id_
        assert str(assoc_row.ceci_stage_node_id) == str(stage_node_row.id_)


# ---------------------------------------------------------------------------
# Ingest tests
# ---------------------------------------------------------------------------

_PIPELINE_YAML = textwrap.dedent("""\
    stages:
      - name: train_fzboost
        classname: FlexZBoostInformer
        module_name: rail.estimation.algos.flexzboost
        nprocess: 1
        aliases:
          output: model
      - name: estimate_fzboost
        classname: FlexZBoostEstimator
        module_name: rail.estimation.algos.flexzboost
        nprocess: 1
    """)

_LOG_SUCCESS = textwrap.dedent("""\
    Executing stage: FlexZBoostEstimator @ 2025-07-20 15:21:23.242275
    Inserting handle into data store.  model: /pz/data/model.pkl, estimate_fzboost
    Inserting handle into data store.  input: /pz/data/test.hdf5, estimate_fzboost
    Inserting handle into data store.  output: /pz/data/inprogress_output.hdf5, estimate_fzboost
    Stage complete: FlexZBoostEstimator @ 2025-07-20 15:21:25.913904 took 0.04 minutes
    """)

_LOG_FAILURE = textwrap.dedent("""\
    Executing stage: FlexZBoostInformer @ 2025-07-20 14:00:00.000000
    Inserting handle into data store.  input: /pz/data/train.hdf5, train_fzboost
    Stage failed: FlexZBoostInformer @ 2025-07-20 14:00:01.000000 after 0.02 minutes
    """)

_LOG_UNPARSEABLE = "This log has no execution markers.\n"

_CONFIG_YAML = """\
inform_fzboost:
  seed: 42
  trainfrac: 0.75
estimate_fzboost:
  chunk_size: 1000
"""


@pytest.fixture()
def config_yaml_file(tmp_path: Path) -> Path:
    p = tmp_path / "pz_config.yml"
    p.write_text(_CONFIG_YAML)
    return p


@pytest.fixture()
def registered_pipeline():
    from plombiere.local_sync import ceci_pipeline

    return ceci_pipeline.create_row(
        name="pz_dp1", description="Photo-z pipeline", structure={"stages": []}, config={}
    )


@pytest.fixture()
def pipeline_yaml_file(tmp_path: Path) -> Path:
    p = tmp_path / "test_pipeline.yaml"
    p.write_text(_PIPELINE_YAML)
    return p


@pytest.fixture()
def log_dir_success(tmp_path: Path) -> Path:
    d = tmp_path / "logs"
    d.mkdir()
    (d / "estimate_fzboost.out").write_text(_LOG_SUCCESS)
    return d


@pytest.fixture()
def log_dir_mixed(tmp_path: Path) -> Path:
    d = tmp_path / "logs"
    d.mkdir()
    (d / "train_fzboost.out").write_text(_LOG_FAILURE)
    (d / "estimate_fzboost.out").write_text(_LOG_SUCCESS)
    return d


@pytest.fixture()
def log_dir_empty(tmp_path: Path) -> Path:
    d = tmp_path / "logs"
    d.mkdir()
    (d / "junk.out").write_text(_LOG_UNPARSEABLE)
    return d


class TestRegisterPipelineFromYaml:
    def test_creates_stage_nodes(self, pipeline_yaml_file: Path):
        from plombiere.ceci_ingest import register_pipeline_from_yaml

        pipeline_create, stage_nodes = register_pipeline_from_yaml(pipeline_yaml_file)
        assert pipeline_create.name == "test_pipeline"
        assert len(stage_nodes) == 2
        names = {n.name for n in stage_nodes}
        assert "FlexZBoostInformer" in names
        assert "FlexZBoostEstimator" in names

    def test_deduplication(self, tmp_path: Path):
        """Same classname appearing twice → one schema node."""
        yaml_content = textwrap.dedent("""\
            stages:
              - name: estimate_a
                classname: FlexZBoostEstimator
                module_name: rail.estimation.algos.flexzboost
              - name: estimate_b
                classname: FlexZBoostEstimator
                module_name: rail.estimation.algos.flexzboost
            """)
        p = tmp_path / "dup.yaml"
        p.write_text(yaml_content)

        from plombiere.ceci_ingest import register_pipeline_from_yaml

        _, stage_nodes = register_pipeline_from_yaml(p)
        assert len(stage_nodes) == 1

    def test_empty_stages_raises(self, tmp_path: Path):
        p = tmp_path / "empty.yaml"
        p.write_text("stages: []\n")

        from plombiere.ceci_ingest import register_pipeline_from_yaml

        with pytest.raises(ValueError, match="No stages found"):
            register_pipeline_from_yaml(p)

    def test_custom_name(self, pipeline_yaml_file: Path):
        from plombiere.ceci_ingest import register_pipeline_from_yaml

        pipeline_create, _ = register_pipeline_from_yaml(pipeline_yaml_file, name="my_pipeline")
        assert pipeline_create.name == "my_pipeline"


class TestIngestStageLogs:
    def test_success_log_creates_records(self, log_dir_success: Path):
        from plombiere.ceci_ingest import ingest_stage_logs
        from tisserande.local_sync import edge

        pipeline_exec, _, stage_results = ingest_stage_logs(log_dir_success)

        assert pipeline_exec.status == ExecutionStatus.SUCCESS
        assert pipeline_exec.duration_seconds is not None

        assert len(stage_results) == 1
        exec_, stage_node, file_nodes = stage_results[0]
        assert exec_.status == ExecutionStatus.SUCCESS
        assert exec_.parent_execution_id == pipeline_exec.id_
        assert stage_node.type_ == "ceci_stage"

        assert len(file_nodes) == 3
        tags = {fn.arg_name for fn in file_nodes}
        assert tags == {"model", "input", "output"}

        edges = edge.get_rows()
        from_stage = [e for e in edges if str(e.from_id) == str(stage_node.id_)]
        assert any(True for e in from_stage)

    def test_inprogress_stripped_from_output_path(self, log_dir_success: Path):
        from plombiere.ceci_ingest import ingest_stage_logs

        _, _, stage_results = ingest_stage_logs(log_dir_success)
        _, _, file_nodes = stage_results[0]
        paths = {fn.path for fn in file_nodes}
        assert not any("inprogress_" in p for p in paths)
        assert "/pz/data/output.hdf5" in paths

    def test_failure_log_sets_failure_status(self, log_dir_mixed: Path):
        from plombiere.ceci_ingest import ingest_stage_logs

        pipeline_exec, _, stage_results = ingest_stage_logs(log_dir_mixed)
        assert pipeline_exec.status == ExecutionStatus.FAILURE
        statuses = {exec_.status for exec_, _, _ in stage_results}
        assert ExecutionStatus.FAILURE in statuses
        assert ExecutionStatus.SUCCESS in statuses

    def test_pipeline_exec_spans_all_stages(self, log_dir_mixed: Path):
        from plombiere.ceci_ingest import ingest_stage_logs

        pipeline_exec, _, stage_results = ingest_stage_logs(log_dir_mixed)
        start_times = [exec_.start_time for exec_, _, _ in stage_results]
        end_times = [exec_.end_time for exec_, _, _ in stage_results]
        assert pipeline_exec.start_time == min(start_times)
        assert pipeline_exec.end_time == max(end_times)

    def test_empty_log_dir_raises(self, log_dir_empty: Path):
        from plombiere.ceci_ingest import ingest_stage_logs

        with pytest.raises(ValueError, match="No parseable stage log files"):
            ingest_stage_logs(log_dir_empty)

    def test_schema_nodes_linked(self, pipeline_yaml_file: Path, log_dir_success: Path):
        from plombiere.ceci_ingest import ingest_stage_logs, register_pipeline_from_yaml

        _, schema_nodes = register_pipeline_from_yaml(pipeline_yaml_file)
        _, _, stage_results = ingest_stage_logs(log_dir_success, schema_nodes=schema_nodes)

        _, stage_node, _ = stage_results[0]
        assert stage_node.ceci_stage_schema_node_id is not None

    def test_stage_exec_links_to_pipeline_exec(self, log_dir_success: Path):
        from plombiere.ceci_ingest import ingest_stage_logs
        from tisserande.local_sync import execution as execution_ops

        pipeline_exec, _, stage_results = ingest_stage_logs(log_dir_success)

        all_executions = execution_ops.get_rows()
        pipeline_ids = {str(e.id_) for e in all_executions if e.parent_execution_id is None}
        assert str(pipeline_exec.id_) in pipeline_ids

        stage_exec, _, _ = stage_results[0]
        assert str(stage_exec.parent_execution_id) == str(pipeline_exec.id_)


class TestIngestStageLogsWithVariant:
    """Tests for the pipeline_variant path of ingest_stage_logs."""

    @pytest.fixture()
    def variant(self, config_yaml_file: Path, registered_pipeline):
        from plombiere.ceci_ingest import register_pipeline_variant_from_yaml

        return register_pipeline_variant_from_yaml(config_yaml_file, registered_pipeline.id_)

    def test_returns_instance_when_variant_given(self, log_dir_success: Path, variant):
        from plombiere.ceci_ingest import ingest_stage_logs

        _, instance, _ = ingest_stage_logs(log_dir_success, pipeline_variant=variant)
        assert instance is not None
        assert instance.id_ is not None

    def test_instance_links_to_variant(self, log_dir_success: Path, variant):
        from plombiere.ceci_ingest import ingest_stage_logs

        _, instance, _ = ingest_stage_logs(log_dir_success, pipeline_variant=variant)
        assert instance.ceci_pipeline_variant_id == variant.id_

    def test_instance_status_matches_pipeline(self, log_dir_success: Path, variant):
        from plombiere.ceci_ingest import ingest_stage_logs

        pipeline_exec, instance, _ = ingest_stage_logs(log_dir_success, pipeline_variant=variant)
        assert instance.status == pipeline_exec.status

    def test_instance_run_date_from_log_start(self, log_dir_success: Path, variant):
        from datetime import date

        from plombiere.ceci_ingest import ingest_stage_logs

        pipeline_exec, instance, _ = ingest_stage_logs(log_dir_success, pipeline_variant=variant)
        assert instance.run_date == pipeline_exec.start_time.date()

    def test_instance_persisted(self, log_dir_success: Path, variant):
        from plombiere.ceci_ingest import ingest_stage_logs
        from plombiere.local_sync import ceci_pipeline_instance

        _, instance, _ = ingest_stage_logs(log_dir_success, pipeline_variant=variant)
        rows = ceci_pipeline_instance.get_rows()
        assert any(str(r.id_) == str(instance.id_) for r in rows)

    def test_no_variant_returns_none_instance(self, log_dir_success: Path):
        from plombiere.ceci_ingest import ingest_stage_logs

        _, instance, _ = ingest_stage_logs(log_dir_success)
        assert instance is None

    def test_failure_pipeline_instance_status(self, log_dir_mixed: Path, variant):
        from plombiere.ceci_ingest import ingest_stage_logs

        _, instance, _ = ingest_stage_logs(log_dir_mixed, pipeline_variant=variant)
        assert instance.status == ExecutionStatus.FAILURE

    def test_instance_has_execution_id(self, log_dir_success: Path, variant):
        from plombiere.ceci_ingest import ingest_stage_logs

        pipeline_exec, instance, _ = ingest_stage_logs(log_dir_success, pipeline_variant=variant)
        assert instance.execution_id == pipeline_exec.id_


class TestRegisterPipelineVariantFromYaml:
    def test_creates_variant(self, config_yaml_file: Path, registered_pipeline):
        from plombiere.ceci_ingest import register_pipeline_variant_from_yaml

        variant = register_pipeline_variant_from_yaml(config_yaml_file, registered_pipeline.id_)
        assert variant.id_ is not None
        assert variant.ceci_pipeline_id == registered_pipeline.id_

    def test_default_name_from_file_stem(self, config_yaml_file: Path, registered_pipeline):
        from plombiere.ceci_ingest import register_pipeline_variant_from_yaml

        variant = register_pipeline_variant_from_yaml(config_yaml_file, registered_pipeline.id_)
        assert variant.name == "pz_config"

    def test_custom_name(self, config_yaml_file: Path, registered_pipeline):
        from plombiere.ceci_ingest import register_pipeline_variant_from_yaml

        variant = register_pipeline_variant_from_yaml(
            config_yaml_file, registered_pipeline.id_, name="gold_sample"
        )
        assert variant.name == "gold_sample"

    def test_overrides_stored_from_yaml(self, config_yaml_file: Path, registered_pipeline):
        from plombiere.ceci_ingest import register_pipeline_variant_from_yaml

        variant = register_pipeline_variant_from_yaml(config_yaml_file, registered_pipeline.id_)
        assert variant.overrides["inform_fzboost"]["seed"] == 42
        assert variant.overrides["estimate_fzboost"]["chunk_size"] == 1000

    def test_extra_description(self, config_yaml_file: Path, registered_pipeline):
        from plombiere.ceci_ingest import register_pipeline_variant_from_yaml

        variant = register_pipeline_variant_from_yaml(
            config_yaml_file, registered_pipeline.id_, extra_description="Gold sample run"
        )
        assert variant.extra_description == "Gold sample run"

    def test_empty_config_yaml(self, tmp_path: Path, registered_pipeline):
        p = tmp_path / "empty_config.yml"
        p.write_text("{}\n")
        from plombiere.ceci_ingest import register_pipeline_variant_from_yaml

        variant = register_pipeline_variant_from_yaml(p, registered_pipeline.id_)
        assert variant.overrides == {}

    def test_variant_persisted(self, config_yaml_file: Path, registered_pipeline):
        from plombiere.ceci_ingest import register_pipeline_variant_from_yaml
        from plombiere.local_sync import ceci_pipeline_variant

        variant = register_pipeline_variant_from_yaml(config_yaml_file, registered_pipeline.id_)
        rows = ceci_pipeline_variant.get_rows()
        assert any(r.id_ == variant.id_ for r in rows)
