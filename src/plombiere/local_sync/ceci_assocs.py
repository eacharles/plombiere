from macon.local_sync.base import SyncOperations

from .. import models
from ..db import ceci_assocs as db
from ..local_async import ceci_assocs as async_ops


class CeciPipelineStageAssocSyncOperations(
    SyncOperations[
        db.CeciPipelineStageAssocTable,
        models.CeciPipelineStageAssoc,
        models.CeciPipelineStageAssocCreate,
    ]
):
    """Synchronous operations for CECI pipeline-stage associations."""


ceci_pipeline_stage_assoc = CeciPipelineStageAssocSyncOperations(
    async_ops.ceci_pipeline_stage_assoc
)
