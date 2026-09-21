-- Active: 1789845362794@@127.0.0.1@5432@E_Commerce
-- Detect customer changes between staged data and the current dimension row.

SELECT
    s.customer_id,
    s.customer_city  AS new_city,
    d.customer_city  AS old_city
FROM stg_customer_updates s
JOIN dim_customer d
    ON s.customer_id = d.customer_id
    AND d.is_current = TRUE
WHERE s.customer_city IS DISTINCT FROM d.customer_city;

-- Rows returned here indicate a change to be handled by SCD logic.