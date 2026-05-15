-- V3__create_orders_table.sql
-- Creates the orders table and supporting indexes.

CREATE TABLE IF NOT EXISTS orders (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    status         VARCHAR(50)     NOT NULL DEFAULT 'pending',
    total_amount   NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    currency       CHAR(3)         NOT NULL DEFAULT 'USD',
    notes          TEXT,
    created_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_orders_status CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')),
    CONSTRAINT chk_orders_total  CHECK (total_amount >= 0)
);

CREATE INDEX IF NOT EXISTS idx_orders_user_id    ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status     ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
