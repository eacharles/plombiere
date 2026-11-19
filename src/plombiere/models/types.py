"""Node type enumerations for CECI-specific nodes."""

import enum


class CeciNodeType(enum.Enum):
    """Discriminator values for CECI node types."""

    CECI_FILE = "ceci_file"
    CECI_STAGE_CALL = "ceci_stage_call"

    @property
    def is_data(self) -> bool:
        return self == CeciNodeType.CECI_FILE

    @property
    def is_logic(self) -> bool:
        return self == CeciNodeType.CECI_STAGE_CALL
