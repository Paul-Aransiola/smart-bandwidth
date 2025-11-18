-- Initialize PostgreSQL Database for Smart Bandwidth Monitor

-- Ensure UTF8 encoding
SET client_encoding = 'UTF8';

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant all privileges to the database user
-- (This is executed after the database is created by POSTGRES_DB)

-- Optional: Create additional users or roles
-- CREATE ROLE readonly_user WITH LOGIN PASSWORD 'readonly_password';
-- GRANT CONNECT ON DATABASE bandwidth_monitor TO readonly_user;
-- GRANT USAGE ON SCHEMA public TO readonly_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;

-- Set default transaction isolation level
ALTER DATABASE bandwidth_monitor SET default_transaction_isolation TO 'read committed';

-- Connection limits (optional)
-- ALTER DATABASE bandwidth_monitor CONNECTION LIMIT 100;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully';
END $$;
