# PostgreSQL Development Setup

## 🔗 Database Connection

- **Host**: `shivi.local`
- **Port**: `32543`
- **Database**: `myapp`
- **Dev User**: `test_user` / `test123`
- **Prod User**: `prod_user` / `prod123`

## 🚀 Local Setup

### 1. Install PostgreSQL Client (if needed)
```bash
# macOS
brew install postgresql

# Ubuntu
sudo apt-get install postgresql-client
```

### 2. Test Connection
```bash
psql postgresql://test_user:test123@shivi.local:32543/myapp -c "SELECT current_user;"
```

### 3. Run Database Setup (if tables don't exist)
```bash
cd khushal_hello_grpc/deployment/postgres

# Create tables
psql postgresql://test_user:test123@shivi.local:32543/myapp -f 01_create_tables.sql

# Insert sample data
psql postgresql://test_user:test123@shivi.local:32543/myapp -f 02_sample_data.sql

# Verify setup
psql postgresql://test_user:test123@shivi.local:32543/myapp -c "SELECT * FROM test.user_orders LIMIT 5;"
```

## 🔌 Application Connection

### Environment Variables
```bash
export DATABASE_URL="postgresql://test_user:test123@shivi.local:32543/myapp"
export DB_SCHEMA="test"
```

### Connection Examples
```python
# Python
import psycopg2
conn = psycopg2.connect(
    "postgresql://test_user:test123@shivi.local:32543/myapp",
    options="-c search_path=test,public"
)
```

```go
// Go
connStr := "host=shivi.local port=32543 user=test_user password=test123 dbname=myapp search_path=test,public sslmode=disable"
db, err := sql.Open("postgres", connStr)
```

## 🏗️ Database Schema

- **`test` schema**: Your development tables (full access)
- **`prod` schema**: Production data (read-only access)

### Tables
- `test.users` - User accounts
- `test.orders` - Order data  
- `test.user_orders` - Joined view of users + orders

## 🛠️ Quick Commands

```bash
# Connect to database
psql postgresql://test_user:test123@shivi.local:32543/myapp

# List tables
psql postgresql://test_user:test123@shivi.local:32543/myapp -c "\dt test.*"

# Sample query
psql postgresql://test_user:test123@shivi.local:32543/myapp -c "SELECT * FROM test.users;"

# Reset test data
psql postgresql://test_user:test123@shivi.local:32543/myapp -c "TRUNCATE test.orders, test.users CASCADE;"

# Re-run sample data
psql postgresql://test_user:test123@shivi.local:32543/myapp -f 02_sample_data.sql
```

## 🌐 Web Interface
- **pgAdmin**: http://shivi.local:32544
- **Login**: admin@admin.com / admin123

## 🔒 Development Notes

- Use `test_user` for development (never modify prod data)
- Use `test` schema for all development work
- Production credentials are for deployment only

---

**Quick Start**: Use `postgresql://test_user:test123@shivi.local:32543/myapp` as your connection string. 