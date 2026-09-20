CREATE OR REPLACE PROCEDURE update_dim_customer_scd1()
LANGUAGE plpgsql
AS $$
BEGIN

    UPDATE dim_customer AS target
    SET
        customer_unique_id = source.customer_unique_id,
        customer_city = source.customer_city,
        customer_state = source.customer_state
    FROM stg_customer_updates AS source
    WHERE target.customer_id = source.customer_id;

END;
$$;

-- CALL update_dim_customer_scd1();