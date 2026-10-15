# tisserande

![Tisserande logo](docs/figures/tisserand_logo_big.jpg)

Execution provenance tracking for Python functions and shell scripts.

Tisserande records **what** functions ran, **what** data they consumed and produced, **how long** they took, and **whether** they succeeded — all as a directed acyclic graph (DAG) stored in a database.

## Installation

```bash
pip install tisserande
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Configure tracking

```python
from tisserande.tracking import configure

# Uses in-memory SQLite by default for quick experiments
configure(db_url="sqlite+aiosqlite:///my_provenance.db")
```

### 2. Decorate your functions

```python
from tisserande.tracking import track
from tisserande.tracking.annotations import DataFile, Param

@track
def fit_model(
    input_catalog: DataFile[str],
    config_file: DataFile[str],
    learning_rate: Param[float],
) -> DataFile[str]:
    """Train a model and write output."""
    # ... your code ...
    return "/data/results/model_output.fits"

# Call normally — provenance is recorded automatically
fit_model("/data/catalogs/train.fits", "/configs/model.yaml", 0.01)
```

### 3. Query the provenance

```python
from tisserande.local_sync import execution, node, edge

# Get all executions
for ex in execution.get_rows():
    print(f"{ex.id_}: status={ex.status}, duration={ex.duration_seconds:.2f}s")

# Get all nodes for a specific execution
nodes = node.filter_rows(filters=[...])
```

## Type Annotations

Control how arguments are classified with type annotations:

```python
from tisserande.tracking.annotations import (
    DataFile,      # File containing data (e.g., FITS, HDF5, Parquet)
    ConfigFile,    # Configuration file (e.g., YAML, JSON, TOML)
    ConfigDict,    # Dictionary containing configuration
    Param,         # Numeric parameter
    ArrayArg,      # Array of values
    ObjectArg,     # Python object
    Untracked,     # Skip tracking for this argument
)
```

Without annotations, tisserande uses heuristics (file extensions, Python types) to classify arguments automatically.

## Tracking Shell Commands

```python
from tisserande.tracking import track_shell

result = track_shell(
    "sextractor input.fits -c config.sex",
    inputs={
        "image": "/data/input.fits",
        "config": "/configs/config.sex",
    },
    outputs={
        "catalog": "/data/output.cat",
    },
)
```

## Async Support

```python
from tisserande.tracking import track_async

@track_async
async def async_pipeline(data: DataFile[str]) -> DataFile[str]:
    # ... async processing ...
    return "/data/output.fits"
```

## Architecture

Tisserande models provenance as a DAG:

```
[input.fits] ──→ [fit_model()] ──→ [output.fits]
[config.yaml] ─┘                    
[lr=0.01] ─────┘
```

- **Nodes** represent data (files, configs, parameters, arrays, objects) and logic (functions, scripts)
- **Edges** connect inputs to functions and functions to outputs
- **Executions** group all nodes/edges from a single function call

The database stores:
- **Type tables**: reusable definitions (e.g., "PythonFunction: fit_model in mymodule")
- **Node table**: specific instances with runtime values
- **Edge table**: directed connections between nodes
- **Execution table**: timing, status, error info per function call

## Database Backends

By default, tisserande uses SQLite via SQLAlchemy. Configure any SQLAlchemy-compatible database:

```python
configure(db_url="postgresql+asyncpg://user:pass@localhost/provenance")
```

## REST API

Start the server:

```bash
tisserande-server --port 8080
```

Provides CRUD endpoints for all tables at `http://localhost:8080/docs`.

## CLI

```bash
# List executions
tisserande-local execution get-rows

# Get a specific node
tisserande-local node get-row <node-uuid>
```

## Configuration

Environment variables (prefix `TISSERANDE__`, nested with `__`):

| Variable | Default | Description |
|----------|---------|-------------|
| `TISSERANDE__DB__URL` | `sqlite+aiosqlite:///tisserande.db` | Database URL |
| `TISSERANDE__TRACKING__ENABLED` | `true` | Global tracking toggle |
| `TISSERANDE__TRACKING__BACKEND` | `local_sync` | Backend: `local_sync` or `null` |

## Testing

For tests, use the `NullBackend` to avoid database overhead:

```python
from tisserande.tracking import configure
from tisserande.tracking.backends import NullBackend

configure(backend=NullBackend())
```

## License

MIT
