"""
Environment and stage management utilities.
"""

import os
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class Stage(Enum):
    """Application deployment stages"""
    DEV = "DEV"
    PROD = "PROD"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def is_dev(self) -> bool:
        """Check if current stage is development"""
        return self == Stage.DEV
    
    @property
    def is_prod(self) -> bool:
        """Check if current stage is production"""
        return self == Stage.PROD


def get_stage() -> Stage:
    """
    Get current application stage from environment variable.
    
    Reads from APP_ENV environment variable.
    Only accepts "PROD" or "DEV" (case-insensitive).
    Defaults to DEV for any other value.
    
    Returns:
        Stage enum value
        
    Examples:
        stage = get_stage()
        if stage.is_prod:
            print("Running in production")
    """
    env_value = os.getenv("APP_ENV", "DEV").upper().strip()
    
    if env_value == "PROD":
        stage = Stage.PROD
    else:
        stage = Stage.DEV
        if env_value != "DEV":
            logger.warning(f"APP_ENV='{env_value}' is not 'PROD' or 'DEV', defaulting to DEV")
    
    logger.debug(f"Application stage: {stage}")
    return stage


def is_development() -> bool:
    """Check if running in development stage"""
    return get_stage().is_dev


def is_production() -> bool:
    """Check if running in production stage"""
    return get_stage().is_prod 