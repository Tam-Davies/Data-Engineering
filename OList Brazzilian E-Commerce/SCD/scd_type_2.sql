-- Type 2: keep history and create a new current version.

-- Close the old active record before creating the new version.
UPDATE dim_customer AS d
SET valid_to = CURRENT_DATE, is_current = FALSE
FROM stg_customer_updates AS s
WHERE d.customer_id = s.customer_id
  AND d.is_current = TRUE
  AND d.customer_city IS DISTINCT FROM s.customer_city;

-- Insert the new current record with a new validity period.
INSERT INTO dim_customer (
    customer_id, customer_unique_id, customer_city, customer_state,
    customer_key, valid_from, valid_to, is_current
)
SELECT
    s.customer_id,
    s.customer_unique_id,
    s.customer_city,
    s.customer_state,
    (SELECT MAX(customer_key) + 1 FROM dim_customer),
    CURRENT_DATE,
    NULL,
    TRUE
FROM stg_customer_updates s
JOIN dim_customer d
    ON s.customer_id = d.customer_id
    AND d.is_current = FALSE
    AND d.valid_to = CURRENT_DATE
WHERE s.customer_city IS DISTINCT FROM d.customer_city;
