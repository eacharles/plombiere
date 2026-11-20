"""Populate a test database from a DOT file describing the pipeline graph.

Run from the project root::

    python scripts/populate_test_db.py               # creates test.db
    python scripts/populate_test_db.py my.db         # custom path
    python scripts/populate_test_db.py --overwrite   # delete and recreate

Place one or more ``*.dot`` files in the project root; each is registered as a
separate pipeline.  Stage nodes (box/rect shape) become CeciStage templates
and file nodes (ellipse shape) become CeciFileType templates.
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
    from tisserande.db.base import Base, init_db

    db_url = f"sqlite+aiosqlite:///{db_path.resolve()}"
    init_db(db_url)

    sync_url = db_url.replace("+aiosqlite", "")
    engine = sa.create_engine(sync_url)
    Base.metadata.create_all(engine)
    engine.dispose()

    print(f"Initialised database: {db_path}")

    # ------------------------------------------------------------------
    # Register every pipeline*.dot file found in the project root
    # ------------------------------------------------------------------
    from plombiere.ceci_pipeline_dot import register_pipeline_from_dot

    dot_files = sorted(ROOT.glob("pipeline*.dot"))
    if not dot_files:
        print("No *.dot files found in project root — nothing to register.")
        print("Create a pipeline.dot file describing your bipartite pipeline graph.")
    else:
        for dot_file in dot_files:
            pipeline, stages, file_types = register_pipeline_from_dot(
                dot_file, name=dot_file.stem, version="1.0"
            )
            print(
                f"Registered '{pipeline.name}': "
                f"{len(stages)} stage templates, {len(file_types)} file type templates"
            )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    from plombiere.local_sync import ceci_pipeline as pipeline_ops
    from tisserande.local_sync import node_template

    print()
    print("=== Summary ===")
    print(f"  pipelines      : {len(pipeline_ops.get_rows())}")
    print(f"  node templates : {len(node_template.get_rows())}")
    print(f"  db             : {db_path.resolve()}")


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
