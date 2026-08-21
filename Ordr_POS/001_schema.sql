-- ============================================================
--  ORDR Restaurant POS — PostgreSQL Schema
--  Run with: psql -U postgres -d ordr_db -f 001_schema.sql
-- ============================================================

-- Create database (run separately as superuser if needed)
-- CREATE DATABASE ordr_db;

-- ── Extensions ──────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- for fast text search

-- ── Staff ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS staff (
    id          VARCHAR(20) PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    role        VARCHAR(50)  NOT NULL,
    pin_hash    VARCHAR(128) NOT NULL,  -- store bcrypt hash, never plain PIN
    active      BOOLEAN      DEFAULT TRUE,
    created_at  TIMESTAMPTZ  DEFAULT NOW()
);

-- ── Tables (restaurant tables) ──────────────────────────────
CREATE TABLE IF NOT EXISTS restaurant_tables (
    id          VARCHAR(10)  PRIMARY KEY,
    number      INTEGER      NOT NULL UNIQUE,
    seats       INTEGER      NOT NULL DEFAULT 4,
    status      VARCHAR(20)  NOT NULL DEFAULT 'available'
                             CHECK (status IN ('available','occupied','reserved')),
    updated_at  TIMESTAMPTZ  DEFAULT NOW()
);

-- ── Menu categories ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS menu_categories (
    id          SERIAL       PRIMARY KEY,
    name        VARCHAR(50)  NOT NULL UNIQUE,
    sort_order  INTEGER      DEFAULT 0
);

-- ── Menu items ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS menu_items (
    id          VARCHAR(20)  PRIMARY KEY,
    category_id INTEGER      REFERENCES menu_categories(id) ON DELETE SET NULL,
    name        VARCHAR(100) NOT NULL,
    price       NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    emoji       VARCHAR(10)  DEFAULT '🍽️',
    active      BOOLEAN      DEFAULT TRUE,
    created_at  TIMESTAMPTZ  DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  DEFAULT NOW()
);

-- ── Orders ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id           VARCHAR(20)  PRIMARY KEY,
    table_id     VARCHAR(10)  REFERENCES restaurant_tables(id) ON DELETE SET NULL,
    staff_id     VARCHAR(20)  REFERENCES staff(id) ON DELETE SET NULL,
    status       VARCHAR(20)  NOT NULL DEFAULT 'pending'
                              CHECK (status IN ('pending','paid','cancelled')),
    note         TEXT,
    subtotal     NUMERIC(10,2) NOT NULL DEFAULT 0,
    tax          NUMERIC(10,2) NOT NULL DEFAULT 0,
    total        NUMERIC(10,2) NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ  DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  DEFAULT NOW()
);

-- ── Order items ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_items (
    id           SERIAL        PRIMARY KEY,
    order_id     VARCHAR(20)   NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id VARCHAR(20)   REFERENCES menu_items(id) ON DELETE SET NULL,
    name         VARCHAR(100)  NOT NULL,  -- snapshot at time of order
    price        NUMERIC(10,2) NOT NULL,  -- snapshot at time of order
    qty          INTEGER       NOT NULL CHECK (qty > 0),
    line_total   NUMERIC(10,2) GENERATED ALWAYS AS (price * qty) STORED
);

-- ── Sales aggregates (populated by pipeline) ────────────────
CREATE TABLE IF NOT EXISTS sales_daily (
    id            SERIAL        PRIMARY KEY,
    date          DATE          NOT NULL UNIQUE,
    total_orders  INTEGER       NOT NULL DEFAULT 0,
    total_revenue NUMERIC(12,2) NOT NULL DEFAULT 0,
    avg_order_val NUMERIC(10,2),
    top_item      VARCHAR(100),
    created_at    TIMESTAMPTZ   DEFAULT NOW(),
    updated_at    TIMESTAMPTZ   DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sales_weekly (
    id            SERIAL        PRIMARY KEY,
    week_start    DATE          NOT NULL UNIQUE,
    week_end      DATE          NOT NULL,
    total_orders  INTEGER       NOT NULL DEFAULT 0,
    total_revenue NUMERIC(12,2) NOT NULL DEFAULT 0,
    avg_order_val NUMERIC(10,2),
    wow_change_pct NUMERIC(6,2),   -- week-over-week % change
    created_at    TIMESTAMPTZ   DEFAULT NOW(),
    updated_at    TIMESTAMPTZ   DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sales_monthly (
    id             SERIAL        PRIMARY KEY,
    year           INTEGER       NOT NULL,
    month          INTEGER       NOT NULL CHECK (month BETWEEN 1 AND 12),
    total_orders   INTEGER       NOT NULL DEFAULT 0,
    total_revenue  NUMERIC(12,2) NOT NULL DEFAULT 0,
    avg_order_val  NUMERIC(10,2),
    mom_change_pct NUMERIC(6,2),   -- month-over-month % change
    UNIQUE(year, month),
    created_at     TIMESTAMPTZ   DEFAULT NOW(),
    updated_at     TIMESTAMPTZ   DEFAULT NOW()
);

-- ── Alert log (records every triggered alert) ────────────────
CREATE TABLE IF NOT EXISTS alert_log (
    id            SERIAL       PRIMARY KEY,
    alert_type    VARCHAR(50)  NOT NULL,  -- 'revenue_drop', 'revenue_spike', etc.
    period        VARCHAR(20)  NOT NULL,  -- 'daily', 'weekly', 'monthly'
    metric        VARCHAR(50)  NOT NULL,
    current_val   NUMERIC(12,2),
    previous_val  NUMERIC(12,2),
    change_pct    NUMERIC(6,2),
    threshold_pct NUMERIC(6,2),
    message       TEXT,
    sent_at       TIMESTAMPTZ  DEFAULT NOW(),
    channels      TEXT[]        -- ['email','slack']
);

-- ── Pipeline run log ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id           SERIAL       PRIMARY KEY,
    run_type     VARCHAR(50)  NOT NULL,
    status       VARCHAR(20)  NOT NULL CHECK (status IN ('success','failed','running')),
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    started_at   TIMESTAMPTZ  DEFAULT NOW(),
    finished_at  TIMESTAMPTZ
);

-- ── Indexes for Power BI & analytics queries ─────────────────
CREATE INDEX IF NOT EXISTS idx_orders_created_at    ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_status        ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_staff         ON orders(staff_id);
CREATE INDEX IF NOT EXISTS idx_orders_table         ON orders(table_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order    ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_menu     ON order_items(menu_item_id);
CREATE INDEX IF NOT EXISTS idx_sales_daily_date     ON sales_daily(date);
CREATE INDEX IF NOT EXISTS idx_alert_log_sent_at    ON alert_log(sent_at);

-- ── Seed data ────────────────────────────────────────────────
INSERT INTO menu_categories (name, sort_order) VALUES
    ('Starters',  1), ('Mains',    2), ('Sides',  3),
    ('Drinks',    4), ('Desserts', 5)
ON CONFLICT (name) DO NOTHING;

INSERT INTO restaurant_tables (id, number, seats) VALUES
    ('1','1',4),('2','2',4),('3','3',4),('4','4',4),
    ('5','5',4),('6','6',4),('7','7',2),('8','8',2),
    ('9','9',2),('10','10',2),('11','11',2),('12','12',2)
ON CONFLICT (id) DO NOTHING;

-- Note: add staff via the app or with bcrypt-hashed PINs
-- Example (PIN "1234" → bcrypt hash):
-- INSERT INTO staff (id, name, role, pin_hash) VALUES
--     ('s1','Amara Osei','Cashier','$2b$12$...');
