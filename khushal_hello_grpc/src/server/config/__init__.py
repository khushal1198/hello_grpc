"""
Configuration management with Pydantic models.
Simple PostgreSQL configuration for all services.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from khushal_hello_grpc.src.common.utils import Stage, get_stage

logger = logging.getLogger(__name__)
_config_cache: Optional[Dict[Stage, "Config"]] = None


class DatabasePoolConfig(BaseModel):
    """Database connection pool configuration"""
    size: int = Field(default=15)
    max_overflow: int = Field(default=3)
    timeout: int = Field(default=30)


class DatabaseConfig(BaseModel):
    """Database configuration"""
    host: str
    port: int = Field(default=5432)
    user: str
    password: str
    database: str
    schema: str = Field(default="test")
    pool: DatabasePoolConfig = Field(default_factory=DatabasePoolConfig)
    
    @property
    def url(self) -> str:
        """Build PostgreSQL connection URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class Config(BaseModel):
    """Main configuration class"""
    database: DatabaseConfig
    
    class Config:
        extra = "allow"
        validate_assignment = True


def get_config(stage: Optional[Stage] = None) -> Config:
    """
    Get typed configuration object.
    
    Args:
        stage: Stage enum (DEV/PROD). If None, uses get_stage()
    
    Examples:
        config = get_config()
        config = get_config(Stage.PROD)
        db_host = config.database.host
        db_url = config.database.url
    """
    global _config_cache
    
    if stage is None:
        stage = get_stage()
    
    if _config_cache and stage in _config_cache:
        return _config_cache[stage]
    
    # Load config file based on stage value
    config_dir = Path(__file__).parent
    config_file = config_dir / f"{stage.value.lower()}.yaml"
    
    if not config_file.exists():
        logger.warning(f"Config file {config_file} not found, falling back to dev.yaml")
        config_file = config_dir / "dev.yaml"
        
    if not config_file.exists():
        raise FileNotFoundError(f"No configuration file found for stage '{stage}'")
    
    # Load and validate
    try:
        with open(config_file, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        config = Config.model_validate(config_dict)
        
        # Cache
        if _config_cache is None:
            _config_cache = {}
        _config_cache[stage] = config
        
        logger.info(f"Loaded {stage} configuration from {config_file}")
        return config
        
    except Exception as e:
        logger.error(f"Configuration validation failed for {stage}: {e}")
        raise ValueError(f"Invalid configuration for stage '{stage}': {e}")


def get_database_url(stage: Optional[Stage] = None) -> str:
    """Get database URL from configuration"""
    config = get_config(stage)
    return config.database.url


def clear_config_cache():
    """Clear configuration cache"""
    global _config_cache
    _config_cache = None


__all__ = [
    "Config",
    "DatabaseConfig", 
    "DatabasePoolConfig",
    "get_config",
    "get_database_url",
    "clear_config_cache"
] 