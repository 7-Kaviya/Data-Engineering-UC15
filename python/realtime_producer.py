"""
REAL-TIME SALES PRODUCER  (simulated ERP sales feed)

There is no live ERP system in this project, so this script plays the part of the
sales module: it creates one sale event every few seconds, stores it in the queue
table and announces it to PostgreSQL with NOTIFY. The consumer picks it up at once.

Run (from the python/ folder):
    python3 realtime_producer.py                  # one event every 2 seconds, until Ctrl+C
    python3 realtime_producer.py --interval 1 --count 30
    python3 realtime_producer.py --bad-every 5    # every 5th event is invalid, to show validation
"""
import argparse
import json
import os
import random
import time
import uuid
from datetime import datetime

import psycopg2

DB = dict(
    host=os.getenv("PGHOST", "localhost"),
    port=int(os.getenv("PGPORT", "5432")),
    dbname=os.getenv("PGDATABASE", "uc15_dw"),
    user=os.getenv("PGUSER", "postgres"),
    password=os.getenv("UC15_DB_PASSWORD", "uc15pass"),
)

# Same categories and prices that appear in Sales_data.csv
CATEGORIES = ["Beauty", "Clothing", "Electronics"]
PRICES = [25, 30, 50, 300, 500]


def make_event(bad=False):
    quantity = random.randint(1, 4)
    if bad:
        quantity = -quantity  # an invalid sale: negative quantity
    return {
        "event_id": str(uuid.uuid4()),
        "event_time": datetime.now().isoformat(timespec="milliseconds"),
        "customer_id": f"CUSTRT{random.randint(1, 9999):04d}",
        "gender": random.choice(["Male", "Female"]),
        "age": random.randint(18, 64),
        "product_category": random.choice(CATEGORIES),
        "quantity": quantity,
        "price_per_unit": random.choice(PRICES),
    }


def main():
    ap = argparse.ArgumentParser(description="Simulated real-time sales feed")
    ap.add_argument("--interval", type=float, default=2.0, help="seconds between events (default 2)")
    ap.add_argument("--count", type=int, default=0, help="number of events, 0 = run until Ctrl+C")
    ap.add_argument("--bad-every", type=int, default=0, help="make every Nth event invalid (0 = never)")
    args = ap.parse_args()

    conn = psycopg2.connect(**DB)
    sent = 0
    print(f"Producer started: one event every {args.interval}s. Press Ctrl+C to stop.")
    try:
        while args.count == 0 or sent < args.count:
            sent += 1
            bad = args.bad_every > 0 and sent % args.bad_every == 0
            event = make_event(bad)
            with conn.cursor() as cur:
                cur.execute("INSERT INTO sales_event_queue (payload) VALUES (%s) RETURNING id", (json.dumps(event),))
                queue_id = cur.fetchone()[0]
                cur.execute("SELECT pg_notify('sales_events', %s)", (str(queue_id),))
            conn.commit()  # the NOTIFY is delivered when this commit happens
            flag = "  <-- invalid on purpose" if bad else ""
            print(f"[{datetime.now():%H:%M:%S}] sent #{sent}: {event['product_category']}, "
                  f"qty {event['quantity']}, price {event['price_per_unit']}{flag}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        conn.close()
        print(f"Producer stopped after {sent} events.")


if __name__ == "__main__":
    main()
