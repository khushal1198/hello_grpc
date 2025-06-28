# UI Service Configuration

PostgreSQL configuration for the UI service with **Pydantic models** for type safety.

## Files

- `test.yaml` - Development PostgreSQL configuration 
- `prod.yaml` - Production PostgreSQL configuration
- `__init__.py` - Pydantic models and configuration loader

## Usage

```python
from khushal_hello_grpc.src.ui.config import get_config

# Get typed configuration object
config = get_config()

# Full type safety and IDE autocomplete
database_url = config.database.url           # str
schema = config.database.schema               # str
pool_size = config.database.pool.size        # int
```

## Environment Selection

```bash
# Use test configuration (default)
export APP_ENV=test

# Use production configuration  
export APP_ENV=prod
```

## Configuration Structure

```yaml
database:
  host: "hostname"
  port: 5432
  user: "username"  
  password: "password"
  database: "database_name"
  schema: "schema_name"
  pool:
    size: 15
    max_overflow: 3
    timeout: 30
```

Same configuration structure as all other services for consistency. 