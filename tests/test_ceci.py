"""Tests for CECI pipeline tables and node type registration."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from plombiere.models import (
    CeciPipeline,
    CeciPipelineCreate,
    CeciPipelineInstance,
    CeciPipelineInstanceCreate,
    CeciPipelineVariant,
    CeciPipelineVariantCreate,
)
from plombiere.models.nodes import CeciFileCreate, CeciStageCallCreate
from plombiere.models.types import CeciNodeType
from tisserande.db.utils import uuid7
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
        CeciPipelineInstance(
            uid_=uuid7(),
            status=ExecutionStatus.SUCCESS,
            run_date=date(2025, 7, 20),
            ceci_pipeline_variant_id=1,
        )
        assert "run_date" in CeciPipelineInstance.col_names_for_table


class TestCeciNodeTypes:
    def test_ceci_file_is_data(self):
        assert CeciNodeType.CECI_FILE.is_data
        assert not CeciNodeType.CECI_FILE.is_logic

    def test_ceci_stage_is_logic(self):
        assert CeciNodeType.CECI_STAGE_CALL.is_logic
        assert not CeciNodeType.CECI_STAGE_CALL.is_data

    def test_ceci_stage_call_create(self):
        obj = CeciStageCallCreate(
            name="FlexZBoostEstimator",
            python_path="rail.estimation.algos.flexzboost.FlexZBoostEstimator",
        )
        assert obj.node_type == "ceci_stage_call"
        assert obj.python_path == "rail.estimation.algos.flexzboost.FlexZBoostEstimator"

    def test_ceci_file_create(self):
        obj = CeciFileCreate(
            file_path="/tmp/output.hdf5",
            creator="ceci",
        )
        assert obj.node_type == "ceci_file"
        assert obj.file_path == "/tmp/output.hdf5"


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
        assert instance_row.uid_ is not None
        instances = ceci_pipeline_instance.get_rows()
        assert any(str(r.uid_) == str(instance_row.uid_) for r in instances)


# ---------------------------------------------------------------------------
# DOT pipeline registration tests
# ---------------------------------------------------------------------------

_PIPELINE_DOT = """\
digraph pz_pipeline {
    // File nodes
    input_catalog [type=input,  label="input_catalog", file_format="FITS"];
    model_file    [type=output, label="model_file",    file_format="pickle"];
    output_pz     [type=output, label="output_pz",     file_format="HDF5"];

    // Stage nodes
    inform   [type=stage, label="Inform",   python_path="rail.stages.Inform"];
    estimate [type=stage, label="Estimate", python_path="rail.stages.Estimate"];

    // Edges
    input_catalog -> inform   [arg_name="input"];
    inform        -> model_file;
    model_file    -> estimate [arg_name="model"];
    input_catalog -> estimate [arg_name="input"];
    estimate      -> output_pz;
}
"""


@pytest.fixture()
def dot_file(tmp_path: Path) -> Path:
    p = tmp_path / "pz_pipeline.dot"
    p.write_text(_PIPELINE_DOT)
    return p


class TestRegisterPipelineFromDot:
    def test_returns_pipeline(self, dot_file: Path):
        from plombiere.ceci_pipeline_dot import register_pipeline_from_dot

        pipeline, _, _ = register_pipeline_from_dot(dot_file, name="pz_pipeline")
        assert pipeline.name == "pz_pipeline"
        assert pipeline.id_ is not None

    def test_stage_count(self, dot_file: Path):
        from plombiere.ceci_pipeline_dot import register_pipeline_from_dot

        _, stages, _ = register_pipeline_from_dot(dot_file, name="pz_pipeline")
        assert len(stages) == 2

    def test_file_type_count(self, dot_file: Path):
        from plombiere.ceci_pipeline_dot import register_pipeline_from_dot

        _, _, file_types = register_pipeline_from_dot(dot_file, name="pz_pipeline")
        assert len(file_types) == 3

    def test_stage_names(self, dot_file: Path):
        from plombiere.ceci_pipeline_dot import register_pipeline_from_dot

        _, stages, _ = register_pipeline_from_dot(dot_file, name="pz_pipeline")
        names = {s.name for s in stages}
        assert names == {"Inform", "Estimate"}

    def test_stage_python_path(self, dot_file: Path):
        from plombiere.ceci_pipeline_dot import register_pipeline_from_dot

        _, stages, _ = register_pipeline_from_dot(dot_file, name="pz_pipeline")
        paths = {s.python_path for s in stages}
        assert "rail.stages.Inform" in paths
        assert "rail.stages.Estimate" in paths

    def test_file_type_formats(self, dot_file: Path):
        from plombiere.ceci_pipeline_dot import register_pipeline_from_dot

        _, _, file_types = register_pipeline_from_dot(dot_file, name="pz_pipeline")
        formats = {f.file_format for f in file_types}
        assert "FITS" in formats
        assert "HDF5" in formats

    def test_assoc_templates_created(self, dot_file: Path):
        from plombiere.ceci_pipeline_dot import register_pipeline_from_dot
        from tisserande.local_sync import assoc_template as assoc_ops

        pipeline, stages, file_types = register_pipeline_from_dot(dot_file, name="pz_pipeline")
        assocs = assoc_ops.get_rows()
        member_ids = {a.node_template_id for a in assocs if a.graph_template_id == pipeline.id_}
        expected_ids = {s.id_ for s in stages} | {f.id_ for f in file_types}
        assert member_ids == expected_ids

    def test_edge_templates_created(self, dot_file: Path):
        from plombiere.ceci_pipeline_dot import register_pipeline_from_dot
        from tisserande.local_sync import edge_template as et_ops

        register_pipeline_from_dot(dot_file, name="pz_pipeline")
        edges = et_ops.get_rows()
        assert len(edges) == 5

    def test_edge_arg_name(self, dot_file: Path):
        from plombiere.ceci_pipeline_dot import register_pipeline_from_dot
        from tisserande.local_sync import edge_template as et_ops

        _, stages, _ = register_pipeline_from_dot(dot_file, name="pz_pipeline")
        inform = next(s for s in stages if s.name == "Inform")
        edges = et_ops.get_rows()
        to_inform = [e for e in edges if e.to_id == inform.id_]
        assert any(e.arg_name == "input" for e in to_inform)

    def test_version_propagated(self, dot_file: Path):
        from plombiere.ceci_pipeline_dot import register_pipeline_from_dot

        pipeline, stages, file_types = register_pipeline_from_dot(
            dot_file, name="pz_pipeline", version="2.0"
        )
        assert pipeline.version == "2.0"
        assert all(s.version == "2.0" for s in stages)
        assert all(f.version == "2.0" for f in file_types)
