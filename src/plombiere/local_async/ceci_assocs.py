from macon.local_async.base import LocalOperations

from .. import models
from ..db import ceci_assocs as db
from ..db_oper import ceci_assocs as ops


class CeciPipelineStageAssocLocalOperations(
    LocalOperations[
        db.CeciPipelineStageAssocTable,
        models.CeciPipelineStageAssoc,
        models.CeciPipelineStageAssocCreate,
    ]
):
    """Async session-managed operations for CECI pipeline-stage associations."""


ceci_pipeline_stage_assoc = CeciPipelineStageAssocLocalOperations(
    ops.ceci_pipeline_stage_assoc
)
