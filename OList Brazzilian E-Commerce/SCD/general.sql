-- Active: 1789845362794@@127.0.0.1@5432@E_Commerce
SELECT customer_id, customer_city 
FROM dim_customer
 WHERE is_current = TRUE
  LIMIT 1 OFFSET 10;


TRUNCATE TABLE stg_customer_updates;

INSERT INTO stg_customer_updates (customer_id, customer_unique_id, customer_city, customer_state, customer_key)
SELECT customer_id, customer_unique_id, 'curitiba', customer_state, customer_key
FROM dim_customer
WHERE customer_id = '00066ccbe787a588c52bd5ff404590e3'
AND is_current = TRUE;


CALL update_dim_customer_scd2();

SELECT customer_id, customer_city, valid_from, valid_to, is_current, customer_key
FROM dim_customer
WHERE customer_id = '00066ccbe787a588c52bd5ff404590e3'
ORDER BY valid_from;