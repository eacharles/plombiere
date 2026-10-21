"""Populate a test database from the project's sample YAML and log files.

Run from the project root:

    python scripts/populate_test_db.py               # creates test.db
    python scripts/populate_test_db.py my.db         # custom path
    python scripts/populate_test_db.py --overwrite   # delete and recreate
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def main(db_path: Path, *, overwrite: bool) -> None:
    if overwrite and db_path.exists():
        db_path.unlink()
        print(f"Deleted existing {db_path}")

    import sqlalchemy as sa

    import plombiere  # noqa: F401 — registers CECI tables
    from plombiere.ceci_ingest import (
        ingest_stage_logs,
        register_pipeline_from_yaml,
        register_pipeline_variant_from_yaml,
    )
    from plombiere.local_sync import ceci_pipeline as pipeline_ops
    from tisserande.db.base import Base, init_db

    db_url = f"sqlite+aiosqlite:///{db_path.resolve()}"
    init_db(db_url)

    sync_url = db_url.replace("+aiosqlite", "")
    engine = sa.create_engine(sync_url)
    Base.metadata.create_all(engine)
    engine.dispose()

    print(f"Initialised database: {db_path}")

    # ------------------------------------------------------------------
    # pz_dp1_4band pipeline
    # ------------------------------------------------------------------
    pz_yaml = ROOT / "pz_dp1_4band.yaml"
    pz_config = ROOT / "pz_dp1_4band_config.yml"
    log_dir = ROOT / "logs"

    pz_create, pz_schema_nodes = register_pipeline_from_yaml(
        pz_yaml,
        description="DP1 photo-z pipeline (4-band)",
    )
    pz_pipeline = pipeline_ops.create_row(**pz_create.model_dump())
    print(f"Registered pipeline '{pz_pipeline.name}' ({len(pz_schema_nodes)} stage classes)")

    pz_variant = register_pipeline_variant_from_yaml(
        pz_config,
        pz_pipeline.id_,
        extra_description="DP1 4-band photo-z run",
    )
    print(f"Registered variant '{pz_variant.name}'")

    pz_exec, pz_instance, pz_stage_results = ingest_stage_logs(
        log_dir,
        schema_nodes=pz_schema_nodes,
        pipeline_variant=pz_variant,
    )
    print(
        f"Ingested pz run: {len(pz_stage_results)} stages, "
        f"status={pz_exec.status.value}, instance={pz_instance.id_}"
    )

    # ------------------------------------------------------------------
    # tomography_dp1_4band pipeline (no logs available)
    # ------------------------------------------------------------------
    tomo_yaml = ROOT / "tomography_dp1_4band.yaml"
    tomo_config = ROOT / "tomography_dp1_4band_config.yml"

    tomo_create, tomo_schema_nodes = register_pipeline_from_yaml(
        tomo_yaml,
        description="DP1 tomography pipeline (4-band)",
    )
    tomo_pipeline = pipeline_ops.create_row(**tomo_create.model_dump())
    print(f"Registered pipeline '{tomo_pipeline.name}' ({len(tomo_schema_nodes)} stage classes)")

    tomo_variant = register_pipeline_variant_from_yaml(
        tomo_config,
        tomo_pipeline.id_,
        extra_description="DP1 4-band tomography run",
    )
    print(f"Registered variant '{tomo_variant.name}'")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    from plombiere.local_sync import ceci_pipeline_instance, ceci_pipeline_variant
    from tisserande.local_sync import execution, node

    print()
    print("=== Summary ===")
    print(f"  pipelines : {len(pipeline_ops.get_rows())}")
    print(f"  variants  : {len(ceci_pipeline_variant.get_rows())}")
    print(f"  instances : {len(ceci_pipeline_instance.get_rows())}")
    print(f"  nodes     : {len(node.get_rows())}")
    print(f"  executions: {len(execution.get_rows())}")
    print(f"  db        : {db_path.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("db", nargs="?", default="test.db", help="SQLite database path")
    parser.add_argument("--overwrite", action="store_true", help="Delete db before populating")
    args = parser.parse_args()

    db_path = Path(args.db)
    if db_path.exists() and not args.overwrite:
        print(f"Error: {db_path} already exists. Use --overwrite to replace it.", file=sys.stderr)
        sys.exit(1)

    main(db_path, overwrite=args.overwrite)
