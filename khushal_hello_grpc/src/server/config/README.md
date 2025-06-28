# Server Configuration System

Simple, type-safe PostgreSQL configuration with automatic file mapping.

## How It Works

Configuration files are automatically loaded based on the stage enum value:

- `Stage.DEV` → `dev.yaml`
- `Stage.PROD` → `prod.yaml`

No mapping needed! Uses `{stage.value.lower()}.yaml` pattern.

## Usage

```python
from khushal_hello_grpc.src.server.config import get_config
from khushal_hello_grpc.src.common.utils import Stage

# Automatic stage detection from APP_ENV
config = get_config()

# Explicit stage
config = get_config(Stage.PROD)

# Type-safe access
db_url = config.database.url
pool_size = config.database.pool.size
```

## Environment Variables

```bash
export APP_ENV=DEV   # Loads dev.yaml
export APP_ENV=PROD  # Loads prod.yaml
# Any other value defaults to DEV
```

## Configuration Files

### dev.yaml (Development)
```yaml
database:
  host: "shivi.local"
  port: 32543
  user: "testuser"
  password: "testpass"
  database: "myapp"
  schema: "test"
  pool:
    size: 15
    max_overflow: 3
    timeout: 30
```

### prod.yaml (Production)
```yaml
database:
  host: "prod.database.com"
  port: 5432
  user: "produser"
  password: "prodpass"
  database: "myapp"
  schema: "prod"
  pool:
    size: 25
    max_overflow: 5
    timeout: 60
```

## Features

- **Type Safety**: Pydantic models with IDE autocomplete
- **Validation**: Invalid config fails fast at startup
- **Caching**: Configurations are cached for performance
- **Fallback**: Missing files fallback to dev.yaml
- **Extensible**: Easy to add new stages (just create new YAML files)

## Example

```python
config = get_config()
print(f"Connecting to: {config.database.url}")
# Connecting to: postgresql://testuser:testpass@shivi.local:32543/myapp
```

## Next Steps

More configuration sections will be added incrementally:
- Server config (port, workers)
- UI config (ports, hosts)  
- Logging config (level, format)
- Feature flags (health checks, metrics) 