-- Active: 1789845362794@@127.0.0.1@5432@E_Commerce
-- Create a staging table for incoming customer changes.

CREATE TABLE IF NOT EXISTS stg_customer_updates AS
SELECT *
FROM dim_customer
WHERE FALSE;

-- Clear old staged records before loading the next change set.
TRUNCATE TABLE stg_customer_updates;

-- Load the current customer rows to compare against the active dimension.
INSERT INTO stg_customer_updates (
    customer_id, customer_unique_id, customer_city, customer_state, customer_key
)
SELECT customer_id, customer_unique_id, customer_city, customer_state, customer_key
FROM dim_customer
WHERE is_current = TRUE
LIMIT 5;