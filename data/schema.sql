PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL DEFAULT 'COMPLETED'
);

CREATE TABLE IF NOT EXISTS refund_eligibility (
    eligibility_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    request_id TEXT NOT NULL UNIQUE,
    order_id TEXT NOT NULL REFERENCES orders(order_id),
    eligibility_status TEXT NOT NULL CHECK (eligibility_status IN ('APPROVED', 'DENIED')),
    reason TEXT
);

CREATE TABLE IF NOT EXISTS refunds (
    refund_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(order_id),
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING'
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    details TEXT
);

CREATE TABLE IF NOT EXISTS email_outbox (
    email_id TEXT PRIMARY KEY,
    refund_id TEXT NOT NULL,
    recipient TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'QUEUED'
);

INSERT OR IGNORE INTO customers VALUES ('C123', 'Alice Johnson', 'alice@example.com');
INSERT OR IGNORE INTO customers VALUES ('C456', 'Bob Smith', 'bob@example.com');
INSERT OR IGNORE INTO customers VALUES ('C789', 'Carol White', 'carol@example.com');
INSERT OR IGNORE INTO orders VALUES ('ORD-001', 'C123', 50.0, 'USD', 'COMPLETED');
INSERT OR IGNORE INTO orders VALUES ('ORD-002', 'C456', 100.0, 'USD', 'COMPLETED');
INSERT OR IGNORE INTO orders VALUES ('ORD-003', 'C789', 75.0, 'USD', 'COMPLETED');
