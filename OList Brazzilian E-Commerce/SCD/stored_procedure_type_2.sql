-- This SCD Type 2 procedure closes the current customer record when a tracked attribute changes, inserts a new active version with the updated values, and preserves historical validity by maintaining valid_from/valid_to and is_current flags.
-- Active: 1789845362794@@127.0.0.1@5432@E_Commerce
CREATE OR REPLACE PROCEDURE update_dim_customer_scd2()
LANGUAGE plpgsql
AS $$
BEGIN

    -- Step 1: close the current row for every customer whose staged
    -- data actually changed.
    UPDATE dim_customer AS d
    SET valid_to = CURRENT_DATE, is_current = FALSE
    FROM stg_customer_updates AS s
    WHERE d.customer_id = s.customer_id
      AND d.is_current = TRUE
      AND d.customer_city IS DISTINCT FROM s.customer_city;

    -- Step 2: insert the new version for those same customers.
    INSERT INTO dim_customer (
        customer_id, customer_unique_id, customer_city, customer_state,
        customer_key, valid_from, valid_to, is_current
    )
    SELECT
        s.customer_id,
        s.customer_unique_id,
        s.customer_city,
        s.customer_state,
        (SELECT MAX(customer_key) FROM dim_customer) + ROW_NUMBER() OVER (),
        CURRENT_DATE,
        NULL,
        TRUE
    FROM stg_customer_updates s
    JOIN dim_customer d
        ON s.customer_id = d.customer_id
        AND d.is_current = FALSE
        AND d.valid_to = CURRENT_DATE
    WHERE s.customer_city IS DISTINCT FROM d.customer_city;

END;
$$;