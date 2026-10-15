from macon.local_async.base import LocalOperations

from .. import models
from ..db import ceci_pipelines as db
from ..db_oper import ceci_pipelines as ops


class CeciPipelineLocalOperations(
    LocalOperations[db.CeciPipelineTable, models.CeciPipeline, models.CeciPipelineCreate]
):
    """Async session-managed operations for CECI pipeline definitions."""


class CeciPipelineVariantLocalOperations(
    LocalOperations[
        db.CeciPipelineVariantTable, models.CeciPipelineVariant, models.CeciPipelineVariantCreate
    ]
):
    """Async session-managed operations for CECI pipeline variants."""


class CeciPipelineInstanceLocalOperations(
    LocalOperations[
        db.CeciPipelineInstanceTable,
        models.CeciPipelineInstance,
        models.CeciPipelineInstanceCreate,
    ]
):
    """Async session-managed operations for CECI pipeline instances."""


ceci_pipeline = CeciPipelineLocalOperations(ops.ceci_pipeline)
ceci_pipeline_variant = CeciPipelineVariantLocalOperations(ops.ceci_pipeline_variant)
ceci_pipeline_instance = CeciPipelineInstanceLocalOperations(ops.ceci_pipeline_instance)
