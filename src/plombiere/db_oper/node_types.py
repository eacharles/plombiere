from macon.db_oper.base import TableContext, TableOperations

from .. import models
from ..db.nodes import CeciFileTypeTable, CeciStageTable


class CeciFileTypeOperations(
    TableOperations[CeciFileTypeTable, models.CeciFileType, models.CeciFileTypeCreate]
):
    """Table operations for CECI file node type templates."""


class CeciStageOperations(
    TableOperations[CeciStageTable, models.CeciStage, models.CeciStageCreate]
):
    """Table operations for CECI stage templates."""


ceci_file_type = CeciFileTypeOperations(TableContext.from_db_class(CeciFileTypeTable))
ceci_stage = CeciStageOperations(TableContext.from_db_class(CeciStageTable))
