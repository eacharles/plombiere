from macon.local_sync.base import SyncOperations

from .. import models
from ..db.nodes import CeciFileTypeTable, CeciStageTable
from ..local_async.node_types import ceci_file_type as async_file_type_ops
from ..local_async.node_types import ceci_stage as async_stage_ops


class CeciFileTypeSyncOperations(
    SyncOperations[CeciFileTypeTable, models.CeciFileType, models.CeciFileTypeCreate]
):
    """Synchronous operations for CECI file node type templates."""


class CeciStageSyncOperations(
    SyncOperations[CeciStageTable, models.CeciStage, models.CeciStageCreate]
):
    """Synchronous operations for CECI stage templates."""


ceci_file_type = CeciFileTypeSyncOperations(async_file_type_ops)
ceci_stage = CeciStageSyncOperations(async_stage_ops)
