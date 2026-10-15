from macon.local_sync.base import SyncOperations

from .. import models
from ..db import ceci_pipelines as db
from ..local_async import ceci_pipelines as async_ops


class CeciPipelineSyncOperations(
    SyncOperations[db.CeciPipelineTable, models.CeciPipeline, models.CeciPipelineCreate]
):
    """Synchronous operations for CECI pipeline definitions."""


class CeciPipelineVariantSyncOperations(
    SyncOperations[
        db.CeciPipelineVariantTable, models.CeciPipelineVariant, models.CeciPipelineVariantCreate
    ]
):
    """Synchronous operations for CECI pipeline variants."""


class CeciPipelineInstanceSyncOperations(
    SyncOperations[
        db.CeciPipelineInstanceTable,
        models.CeciPipelineInstance,
        models.CeciPipelineInstanceCreate,
    ]
):
    """Synchronous operations for CECI pipeline instances."""


ceci_pipeline = CeciPipelineSyncOperations(async_ops.ceci_pipeline)
ceci_pipeline_variant = CeciPipelineVariantSyncOperations(async_ops.ceci_pipeline_variant)
ceci_pipeline_instance = CeciPipelineInstanceSyncOperations(async_ops.ceci_pipeline_instance)
