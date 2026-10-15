from macon.db_oper.base import TableContext, TableOperations

from .. import models
from ..db import ceci_pipelines as db


class CeciPipelineOperations(
    TableOperations[db.CeciPipelineTable, models.CeciPipeline, models.CeciPipelineCreate]
):
    """Table operations for CECI pipeline definitions."""


class CeciPipelineVariantOperations(
    TableOperations[
        db.CeciPipelineVariantTable, models.CeciPipelineVariant, models.CeciPipelineVariantCreate
    ]
):
    """Table operations for CECI pipeline variants."""


class CeciPipelineInstanceOperations(
    TableOperations[
        db.CeciPipelineInstanceTable, models.CeciPipelineInstance, models.CeciPipelineInstanceCreate
    ]
):
    """Table operations for CECI pipeline instances."""


ceci_pipeline = CeciPipelineOperations(TableContext.from_db_class(db.CeciPipelineTable))
ceci_pipeline_variant = CeciPipelineVariantOperations(
    TableContext.from_db_class(db.CeciPipelineVariantTable)
)
ceci_pipeline_instance = CeciPipelineInstanceOperations(
    TableContext.from_db_class(db.CeciPipelineInstanceTable)
)
