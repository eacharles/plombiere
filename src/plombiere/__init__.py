from ._version import __version__
from .db import ceci_assocs as _assocs  # noqa: F401 — registers tables with tisserande's Base
from .db import ceci_pipelines as _pipelines  # noqa: F401 — registers tables with tisserande's Base
from .db import nodes as _nodes  # noqa: F401 — registers node tables + tisserande type maps

__all__ = ["__version__"]
