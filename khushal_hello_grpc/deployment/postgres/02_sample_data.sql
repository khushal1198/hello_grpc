-- Sample Data for Development and Testing
-- This file populates the test schema with sample data for development

-- =============================================================================
-- CLEAR EXISTING TEST DATA (if any)
-- =============================================================================

-- Clear orders first (due to foreign key constraints)
TRUNCATE test.orders RESTART IDENTITY CASCADE;
TRUNCATE test.users RESTART IDENTITY CASCADE;

-- =============================================================================
-- SAMPLE USERS
-- =============================================================================

INSERT INTO test.users (name, email, is_active, metadata) VALUES 
    ('John Doe', 'john.doe@example.com', true, '{"role": "admin", "preferences": {"theme": "dark"}}'),
    ('Jane Smith', 'jane.smith@example.com', true, '{"role": "user", "preferences": {"theme": "light", "notifications": true}}'),
    ('Bob Johnson', 'bob.johnson@example.com', true, '{"role": "user", "department": "engineering"}'),
    ('Alice Brown', 'alice.brown@example.com', false, '{"role": "user", "last_login": "2024-01-15"}'),
    ('Charlie Wilson', 'charlie.wilson@example.com', true, '{"role": "moderator", "permissions": ["read", "write"]}'),
    ('Diana Davis', 'diana.davis@example.com', true, '{"role": "user", "subscription": "premium"}'),
    ('Eve Anderson', 'eve.anderson@example.com', true, '{"role": "user", "location": "US"}'),
    ('Frank Miller', 'frank.miller@example.com', true, '{"role": "user", "verified": true}'),
    ('Grace Taylor', 'grace.taylor@example.com', false, '{"role": "user", "suspended": true}'),
    ('Henry Moore', 'henry.moore@example.com', true, '{"role": "user", "beta_tester": true}');

-- =============================================================================
-- SAMPLE ORDERS
-- =============================================================================

INSERT INTO test.orders (user_id, order_number, total_amount, status, order_data) VALUES 
    (1, 'ORD-2024-001', 99.99, 'completed', '{"items": [{"id": 1, "name": "Widget A", "quantity": 2, "price": 49.99}], "shipping": "express"}'),
    (1, 'ORD-2024-002', 149.50, 'processing', '{"items": [{"id": 2, "name": "Widget B", "quantity": 1, "price": 149.50}], "shipping": "standard"}'),
    (2, 'ORD-2024-003', 75.25, 'completed', '{"items": [{"id": 3, "name": "Gadget X", "quantity": 3, "price": 25.08}], "discount": 0.15}'),
    (2, 'ORD-2024-004', 200.00, 'pending', '{"items": [{"id": 4, "name": "Premium Item", "quantity": 1, "price": 200.00}], "gift_wrap": true}'),
    (3, 'ORD-2024-005', 45.99, 'completed', '{"items": [{"id": 5, "name": "Basic Item", "quantity": 1, "price": 45.99}]}'),
    (5, 'ORD-2024-006', 299.99, 'processing', '{"items": [{"id": 6, "name": "Deluxe Package", "quantity": 1, "price": 299.99}], "priority": "high"}'),
    (6, 'ORD-2024-007', 89.99, 'completed', '{"items": [{"id": 7, "name": "Subscription", "quantity": 1, "price": 89.99}], "recurring": true}'),
    (6, 'ORD-2024-008', 15.50, 'cancelled', '{"items": [{"id": 8, "name": "Small Item", "quantity": 1, "price": 15.50}], "cancel_reason": "customer_request"}'),
    (7, 'ORD-2024-009', 125.75, 'processing', '{"items": [{"id": 9, "name": "Bundle Deal", "quantity": 1, "price": 125.75}], "bundle": true}'),
    (8, 'ORD-2024-010', 67.30, 'completed', '{"items": [{"id": 10, "name": "Regular Item", "quantity": 2, "price": 33.65}]}'),
    (10, 'ORD-2024-011', 449.99, 'pending', '{"items": [{"id": 11, "name": "Beta Product", "quantity": 1, "price": 449.99}], "beta": true}');

-- =============================================================================
-- UPDATE TIMESTAMPS FOR REALISTIC DATA
-- =============================================================================

-- Make some orders appear older for realistic testing
UPDATE test.orders SET 
    created_at = CURRENT_TIMESTAMP - INTERVAL '7 days',
    updated_at = CURRENT_TIMESTAMP - INTERVAL '7 days'
WHERE order_number IN ('ORD-2024-001', 'ORD-2024-003', 'ORD-2024-005');

UPDATE test.orders SET 
    created_at = CURRENT_TIMESTAMP - INTERVAL '3 days',
    updated_at = CURRENT_TIMESTAMP - INTERVAL '2 days'
WHERE order_number IN ('ORD-2024-002', 'ORD-2024-004', 'ORD-2024-006');

UPDATE test.orders SET 
    created_at = CURRENT_TIMESTAMP - INTERVAL '1 day',
    updated_at = CURRENT_TIMESTAMP - INTERVAL '12 hours'
WHERE order_number IN ('ORD-2024-007', 'ORD-2024-008');

-- Make some users appear to have been created earlier
UPDATE test.users SET 
    created_at = CURRENT_TIMESTAMP - INTERVAL '30 days',
    updated_at = CURRENT_TIMESTAMP - INTERVAL '15 days'
WHERE email IN ('john.doe@example.com', 'jane.smith@example.com');

UPDATE test.users SET 
    created_at = CURRENT_TIMESTAMP - INTERVAL '15 days',
    updated_at = CURRENT_TIMESTAMP - INTERVAL '7 days'
WHERE email IN ('bob.johnson@example.com', 'alice.brown@example.com');

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Show what was created
DO $$
DECLARE
    user_count INTEGER;
    order_count INTEGER;
    completed_orders INTEGER;
    total_revenue DECIMAL(10,2);
BEGIN
    SELECT COUNT(*) INTO user_count FROM test.users;
    SELECT COUNT(*) INTO order_count FROM test.orders;
    SELECT COUNT(*) INTO completed_orders FROM test.orders WHERE status = 'completed';
    SELECT COALESCE(SUM(total_amount), 0) INTO total_revenue FROM test.orders WHERE status = 'completed';
    
    RAISE NOTICE '=================================';
    RAISE NOTICE 'Sample data inserted successfully!';
    RAISE NOTICE '=================================';
    RAISE NOTICE 'Users created: %', user_count;
    RAISE NOTICE 'Orders created: %', order_count;
    RAISE NOTICE 'Completed orders: %', completed_orders;
    RAISE NOTICE 'Total revenue: $%', total_revenue;
    RAISE NOTICE '=================================';
    RAISE NOTICE 'Test with: SELECT * FROM test.user_orders;';
END
$$; 