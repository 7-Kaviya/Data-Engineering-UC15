"""
REAL-TIME SALES CONSUMER

Waits for events and loads each one into FactSalesRealtime the moment it arrives.
It listens on a PostgreSQL channel (LISTEN / NOTIFY), so there is no polling delay.

For every event it:
  1. validates it (quantity above zero, known category, date exists in DimDate)
  2. calculates total_amount and the date key
  3. inserts it into FactSalesRealtime and marks the queue row LOADED
     (or REJECTED with the reason, so bad data never reaches the fact table)

If the consumer was stopped, the events that arrived meanwhile stay in the queue
with status NEW and are loaded when the consumer starts again. No event is lost.

Run (from the python/ folder, after sql/06_realtime_setup.sql):
    python3 realtime_consumer.py
Stop with Ctrl+C.
"""
import os
import select
from datetime import datetime

import psycopg2

DB = dict(
    host=os.getenv("PGHOST", "localhost"),
    port=int(os.getenv("PGPORT", "5432")),
    dbname=os.getenv("PGDATABASE", "uc15_dw"),
    user=os.getenv("PGUSER", "postgres"),
    password=os.getenv("UC15_DB_PASSWORD", "uc15pass"),
)
CATEGORIES = {"Beauty", "Clothing", "Electronics"}


def log(msg):
    print(f"[{datetime.now():%H:%M:%S.%f}"[:-3] + f"] {msg}", flush=True)


def validate(ev, cur):
    """Return an error text, or None when the event is valid."""
    if ev.get("quantity", 0) <= 0:
        return "quantity must be above zero"
    if ev.get("price_per_unit", 0) <= 0:
        return "price must be above zero"
    if ev.get("product_category") not in CATEGORIES:
        return "unknown product category"
    date_key = int(datetime.fromisoformat(ev["event_time"]).strftime("%Y%m%d"))
    cur.execute("SELECT 1 FROM dimdate WHERE date_key = %s", (date_key,))
    if cur.fetchone() is None:
        return f"date key {date_key} not found in DimDate"
    return None


def process_new_events(work):
    """Load every queue row that is still NEW. Returns how many were handled."""
    handled = 0
    with work.cursor() as cur:
        cur.execute("SELECT id, payload FROM sales_event_queue WHERE status = 'NEW' "
                    "ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 200")
        for queue_id, ev in cur.fetchall():
            error = validate(ev, cur)
            if error:
                cur.execute("UPDATE sales_event_queue SET status='REJECTED', error=%s, processed_at=%s WHERE id=%s",
                            (error, datetime.now(), queue_id))
                log(f"REJECTED event {queue_id}: {error}")
            else:
                event_time = datetime.fromisoformat(ev["event_time"])
                date_key = int(event_time.strftime("%Y%m%d"))
                total = ev["quantity"] * ev["price_per_unit"]
                now = datetime.now()
                cur.execute(
                    "INSERT INTO FactSalesRealtime (event_id, date_key, customer_id, gender, age, product_category, "
                    "quantity, price_per_unit, total_amount, event_time, ingested_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (event_id) DO NOTHING",
                    (ev["event_id"], date_key, ev["customer_id"], ev["gender"], ev["age"], ev["product_category"],
                     ev["quantity"], ev["price_per_unit"], total, event_time, now))
                cur.execute("UPDATE sales_event_queue SET status='LOADED', processed_at=%s WHERE id=%s", (now, queue_id))
                latency = int((now - event_time).total_seconds() * 1000)
                log(f"loaded event {queue_id}: {ev['product_category']}, qty {ev['quantity']}, total {total}, latency {latency} ms")
            handled += 1
    work.commit()
    return handled


def main():
    listen = psycopg2.connect(**DB)
    listen.autocommit = True
    with listen.cursor() as cur:
        cur.execute("LISTEN sales_events")
    work = psycopg2.connect(**DB)

    backlog = process_new_events(work)  # events that arrived while we were not running
    log(f"Consumer started. Backlog handled: {backlog}. Waiting for events (Ctrl+C to stop).")
    try:
        while True:
            # wait up to 5 seconds for a NOTIFY; the timeout also catches anything missed
            ready, _, _ = select.select([listen], [], [], 5)
            if ready:
                listen.poll()
                listen.notifies.clear()
            process_new_events(work)
    except KeyboardInterrupt:
        pass
    finally:
        listen.close()
        work.close()
        log("Consumer stopped.")


if __name__ == "__main__":
    main()
