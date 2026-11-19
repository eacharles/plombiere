from macon.local_async.base import LocalOperations

from .. import models
from ..db.nodes import CeciFileTypeTable, CeciStageTable
from ..db_oper.node_types import ceci_file_type as ceci_file_type_ops
from ..db_oper.node_types import ceci_stage as ceci_stage_ops


class CeciFileTypeLocalOperations(
    LocalOperations[CeciFileTypeTable, models.CeciFileType, models.CeciFileTypeCreate]
):
    """Async session-managed operations for CECI file node type templates."""


class CeciStageLocalOperations(
    LocalOperations[CeciStageTable, models.CeciStage, models.CeciStageCreate]
):
    """Async session-managed operations for CECI stage templates."""


ceci_file_type = CeciFileTypeLocalOperations(ceci_file_type_ops)
ceci_stage = CeciStageLocalOperations(ceci_stage_ops)
