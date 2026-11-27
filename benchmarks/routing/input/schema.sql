CREATE TABLE customers (id SERIAL PRIMARY KEY, email TEXT UNIQUE NOT NULL, vip BOOLEAN DEFAULT FALSE);
CREATE TABLE products (sku TEXT PRIMARY KEY, name TEXT NOT NULL, price_cents INT NOT NULL, stock INT NOT NULL);
CREATE TABLE orders (id SERIAL PRIMARY KEY, customer_id INT NOT NULL REFERENCES customers(id),
  state TEXT NOT NULL, coupon TEXT, paid_cents INT DEFAULT 0, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE order_lines (order_id INT REFERENCES orders(id), sku TEXT REFERENCES products(sku),
  quantity INT NOT NULL, PRIMARY KEY (order_id, sku));
CREATE TABLE refunds (id SERIAL PRIMARY KEY, order_id INT NOT NULL REFERENCES orders(id), reason TEXT,
  status TEXT NOT NULL, reviewer_id INT REFERENCES staff(id));
CREATE TABLE staff (id SERIAL PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL);
CREATE TABLE shipments (id SERIAL PRIMARY KEY, order_id INT UNIQUE REFERENCES orders(id), carrier TEXT,
  tracking TEXT, shipped_at TIMESTAMPTZ, delivered_at TIMESTAMPTZ);
