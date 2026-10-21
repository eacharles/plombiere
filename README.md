# plombiere

![Plombiere logo](docs/figures/plombiere.jpg)

CECI pipeline provenance tracking, built on [tisserande](https://github.com/eacharles/tisserande).

Plombiere extends tisserande with support for [CECI](https://github.com/LSSTDESC/ceci) pipelines — reading their YAML definitions and stage log files to populate a provenance database.

## Installation

```bash
pip install plombiere
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Initialise the database

```python
from tisserande.db.base import init_db
import plombiere  # registers CECI tables with the database

init_db("sqlite+aiosqlite:///provenance.db")
```

### 2. Register a pipeline definition

```python
from plombiere.ceci_ingest import register_pipeline_from_yaml
from plombiere.local_sync import ceci_pipeline as pipeline_ops

pipeline_create, schema_nodes = register_pipeline_from_yaml(
    "pz_dp1_6band.yaml",
    description="DP1 photo-z pipeline",
)
pipeline = pipeline_ops.create_row(**pipeline_create.model_dump())
print(f"Registered pipeline '{pipeline.name}' with {len(schema_nodes)} stage classes")
```

### 3. Register a pipeline variant

A *variant* captures a specific configuration (overrides) applied to a pipeline.

```python
from plombiere.ceci_ingest import register_pipeline_variant_from_yaml

variant = register_pipeline_variant_from_yaml(
    "pz_dp1_6band_config.yml",
    pipeline.id_,
    extra_description="DP1 4-band run",
)
print(f"Registered variant '{variant.name}'")
```

### 4. Ingest a pipeline run

Passing the variant creates a `CeciPipelineInstance` linking the run to the variant.

```python
from plombiere.ceci_ingest import ingest_stage_logs

pipeline_exec, instance, stage_results = ingest_stage_logs(
    "logs/",
    schema_nodes=schema_nodes,
    pipeline_variant=variant,
)

print(f"Pipeline status: {pipeline_exec.status}")
print(f"Duration: {pipeline_exec.duration_seconds:.1f}s")
print(f"Instance id: {instance.id_}")

for exec_, stage_node, file_nodes in stage_results:
    print(f"  {stage_node.name}: {exec_.status} ({len(file_nodes)} file handles)")
```

### 5. Query the provenance

```python
from plombiere.local_sync import ceci_pipeline, ceci_pipeline_instance, ceci_pipeline_variant
from tisserande.local_sync import node, edge, execution

# CECI-specific tables
for p in ceci_pipeline.get_rows():
    print(p.name)

for v in ceci_pipeline_variant.get_rows():
    print(v.name, v.ceci_pipeline_id)

for i in ceci_pipeline_instance.get_rows():
    print(i.id_, i.status, i.run_date)

# Base tisserande tables — all stage/file nodes live here too
for ex in execution.get_rows():
    print(ex.id_, ex.status, ex.duration_seconds)
```

## What plombiere tracks

**From a pipeline YAML** (`register_pipeline_from_yaml` + `ceci_pipeline.create_row`):
- One `CeciStageNode` (schema node) per unique stage *class* — deduplicated across pipeline steps that reuse the same algorithm.
- A `CeciPipeline` record storing the full YAML structure and default config.

**From a config YAML** (`register_pipeline_variant_from_yaml`):
- A `CeciPipelineVariant` record storing the config overrides and a FK to its parent `CeciPipeline`.

**From stage log files** (`ingest_stage_logs`):
- One pipeline-level `Execution` spanning all stages.
- One stage-level `Execution` per `*.out` log file, parented to the pipeline execution.
- One `CeciStageNode` instance per stage run, linked to its schema node.
- One `CeciFileNode` per `Inserting handle into data store.` log line, with the `inprogress_` prefix stripped from output paths.
- `Edge` records connecting file nodes to stage nodes (input: file → stage; output: stage → file).
- If `pipeline_variant` is supplied: a `CeciPipelineInstance` linked to that variant, with status and run date derived from the logs.

## Data model

```
CeciPipeline
  └── CeciPipelineVariant(s)
        └── CeciPipelineInstance(s)

CeciPipeline ──[assoc]──> CeciStageNode (schema)
                                └── CeciStageNode (instance, per run)
                                      ├── CeciFileNode (input)  ──→ stage
                                      └── CeciFileNode (output) ←── stage
```

All node and edge records are stored in tisserande's core tables and participate in the full tisserande provenance graph.

## Architecture

Plombiere is a plugin package. Importing it registers its SQLAlchemy tables with tisserande's `Base` and its node types with tisserande's dispatch layer, so a single `Base.metadata.create_all()` call creates all tables from both packages.

```python
import plombiere           # one import wires everything up
from tisserande.db.base import init_db, Base
init_db("sqlite+aiosqlite:///my.db")
# ... Base.metadata now includes all plombiere tables
```

## License

MIT
