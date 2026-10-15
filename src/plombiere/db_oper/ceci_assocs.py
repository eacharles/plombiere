from macon.db_oper.base import TableContext, TableOperations

from .. import models
from ..db import ceci_assocs as db


class CeciPipelineStageAssocOperations(
    TableOperations[
        db.CeciPipelineStageAssocTable,
        models.CeciPipelineStageAssoc,
        models.CeciPipelineStageAssocCreate,
    ]
):
    """Table operations for CECI pipeline-stage associations."""


ceci_pipeline_stage_assoc = CeciPipelineStageAssocOperations(
    TableContext.from_db_class(db.CeciPipelineStageAssocTable)
)
