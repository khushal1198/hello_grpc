-- Create Tables for both Test and Production Schemas
-- This file creates the core application tables

-- =============================================================================
-- USERS TABLE
-- =============================================================================

-- Test schema users table
CREATE TABLE IF NOT EXISTS test.users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Production schema users table
CREATE TABLE IF NOT EXISTS prod.users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- =============================================================================
-- ORDERS TABLE
-- =============================================================================

-- Test schema orders table
CREATE TABLE IF NOT EXISTS test.orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES test.users(id) ON DELETE CASCADE,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    order_data JSONB DEFAULT '{}'::jsonb
);

-- Production schema orders table
CREATE TABLE IF NOT EXISTS prod.orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES prod.users(id) ON DELETE CASCADE,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    order_data JSONB DEFAULT '{}'::jsonb
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Test schema indexes
CREATE INDEX IF NOT EXISTS idx_test_users_email ON test.users(email);
CREATE INDEX IF NOT EXISTS idx_test_users_created_at ON test.users(created_at);
CREATE INDEX IF NOT EXISTS idx_test_orders_user_id ON test.orders(user_id);
CREATE INDEX IF NOT EXISTS idx_test_orders_status ON test.orders(status);
CREATE INDEX IF NOT EXISTS idx_test_orders_created_at ON test.orders(created_at);
CREATE INDEX IF NOT EXISTS idx_test_orders_order_number ON test.orders(order_number);

-- Production schema indexes
CREATE INDEX IF NOT EXISTS idx_prod_users_email ON prod.users(email);
CREATE INDEX IF NOT EXISTS idx_prod_users_created_at ON prod.users(created_at);
CREATE INDEX IF NOT EXISTS idx_prod_orders_user_id ON prod.orders(user_id);
CREATE INDEX IF NOT EXISTS idx_prod_orders_status ON prod.orders(status);
CREATE INDEX IF NOT EXISTS idx_prod_orders_created_at ON prod.orders(created_at);
CREATE INDEX IF NOT EXISTS idx_prod_orders_order_number ON prod.orders(order_number);

-- =============================================================================
-- VIEWS FOR CONVENIENCE
-- =============================================================================

-- Test schema view: Join users with their orders
CREATE OR REPLACE VIEW test.user_orders AS
SELECT 
    u.id as user_id,
    u.name as user_name,
    u.email as user_email,
    u.created_at as user_created_at,
    o.id as order_id,
    o.order_number,
    o.total_amount,
    o.status as order_status,
    o.created_at as order_created_at
FROM test.users u
LEFT JOIN test.orders o ON u.id = o.user_id;

-- Production schema view: Join users with their orders
CREATE OR REPLACE VIEW prod.user_orders AS
SELECT 
    u.id as user_id,
    u.name as user_name,
    u.email as user_email,
    u.created_at as user_created_at,
    o.id as order_id,
    o.order_number,
    o.total_amount,
    o.status as order_status,
    o.created_at as order_created_at
FROM prod.users u
LEFT JOIN prod.orders o ON u.id = o.user_id;

-- =============================================================================
-- TRIGGERS FOR UPDATED_AT
-- =============================================================================

-- Function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Test schema triggers
DROP TRIGGER IF EXISTS trigger_test_users_updated_at ON test.users;
CREATE TRIGGER trigger_test_users_updated_at
    BEFORE UPDATE ON test.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_test_orders_updated_at ON test.orders;
CREATE TRIGGER trigger_test_orders_updated_at
    BEFORE UPDATE ON test.orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Production schema triggers
DROP TRIGGER IF EXISTS trigger_prod_users_updated_at ON prod.users;
CREATE TRIGGER trigger_prod_users_updated_at
    BEFORE UPDATE ON prod.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_prod_orders_updated_at ON prod.orders;
CREATE TRIGGER trigger_prod_orders_updated_at
    BEFORE UPDATE ON prod.orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE test.users IS 'Test environment user accounts';
COMMENT ON TABLE prod.users IS 'Production environment user accounts';
COMMENT ON TABLE test.orders IS 'Test environment orders';
COMMENT ON TABLE prod.orders IS 'Production environment orders';

COMMENT ON COLUMN test.users.metadata IS 'Additional user data stored as JSON';
COMMENT ON COLUMN prod.users.metadata IS 'Additional user data stored as JSON';
COMMENT ON COLUMN test.orders.order_data IS 'Additional order data stored as JSON';
COMMENT ON COLUMN prod.orders.order_data IS 'Additional order data stored as JSON';

-- =============================================================================
-- SUCCESS MESSAGE
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Tables created successfully for both test and prod schemas!';
    RAISE NOTICE 'Tables: users, orders';
    RAISE NOTICE 'Views: user_orders';
    RAISE NOTICE 'Triggers: updated_at auto-update';
END
$$; 