"""
ClinNote configuration package.

Exposes all config objects for convenient import:
    from configs import PATHS, MODEL_CFG, DATA_CFG, PIPELINE_CFG
"""

from configs.paths import PATHS
from configs.model_config import MODEL_CFG
from configs.data_config import DATA_CFG
from configs.pipeline_config import PIPELINE_CFG

__all__ = ["PATHS", "MODEL_CFG", "DATA_CFG", "PIPELINE_CFG"]
