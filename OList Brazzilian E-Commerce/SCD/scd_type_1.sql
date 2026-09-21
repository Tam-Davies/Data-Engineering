-- Active: 1789845362794@@127.0.0.1@5432@E_Commerce
-- Type 1: overwrite the current value without keeping history.

UPDATE dim_customer AS target
SET
    customer_city  = source.customer_city,
    customer_state = source.customer_state
FROM stg_customer_updates AS source
WHERE target.customer_id = source.customer_id
  AND target.is_current = TRUE
  AND target.customer_city IS DISTINCT FROM source.customer_city;